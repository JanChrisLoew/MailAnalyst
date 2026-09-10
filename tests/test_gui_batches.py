"""Large GUI tables, late errors and cancellation during visible export."""

import json
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from mailanalyst.checks.preflight import PreflightResult
from mailanalyst.parsing.dispatch import parse_mail_file
from mailanalyst.hashing import file_signature
from mailanalyst.exports.dispatch import _write_output
from tests.samples import create_sources
import tests.test_gui as gui_tests


class GuiBatchTests(unittest.TestCase):
    setUp = gui_tests.GuiTests.setUp
    close_app = gui_tests.GuiTests.close_app
    wait_for = gui_tests.GuiTests.wait_for

    def prepare(self, source):
        self.wait_for(lambda: bool(self.app.system_check_results))
        self.app.input_path.set(str(source))
        self.app.output_dir.set(str(self.root / "output"))
        self.app.preflight_step._start_preflight()
        self.wait_for(lambda: bool(self.app.preflight_results))

    def test_50000_sources_page_filter_and_global_selection(self):
        self.wait_for(lambda: bool(self.app.system_check_results))
        step = self.app.preflight_step
        rows = [PreflightResult(f"synthetic-{i}.eml", ".eml", 100, 0,
                                "warning" if i % 1000 == 999 else "ok", "synthetic", True) for i in range(50000)]
        step._finish_preflight(rows)
        self.assertEqual(len(step.preflight_table.get_children()), 500)
        step.pager.move(1)
        self.assertEqual(step.preflight_table.get_children()[0], "500")
        step.preflight_table.selection_set("500")
        step._toggle_preflight_item()
        self.assertFalse(rows[500].include)
        self.assertTrue(rows[0].include)
        step.pager.filter.set("Warnungen")
        step.pager.refresh(reset=True)
        self.assertEqual(step.pager.total, 50)
        self.assertEqual(step.preflight_table.get_children()[0], "999")
        step._set_status_included("warning", False)
        self.assertTrue(all(not row.include for row in rows if row.status == "warning"))
        self.assertEqual(len(step.preflight_table.get_children()), 50)

    def test_archive_result_pages_find_errors_after_preview(self):
        source = create_sources(self.root)
        seed = source / "first.eml"
        template = parse_mail_file(seed, file_signature(seed, include_hash=True), "Europe/Berlin")[0]
        archive = self.root / "synthetic.pst"
        archive.write_bytes(b"!BDN synthetic placeholder")
        self.prepare(archive)

        def rows(path, signature, *_):
            for i in range(1201):
                yield {**template, **signature.__dict__, "source_file_path": signature.key,
                       "subject": f"Synthetic {i}", "source_path": f"{signature.key}::Synthetic::{i}",
                       "parse_status": "error" if i == 1200 else "ok", "parse_error": "late error" if i == 1200 else ""}

        with patch("mailanalyst.batch_sources.iter_mail_file", side_effect=rows):
            self.app.processing_step._start_processing()
            self.wait_for(lambda: self.app.current_step == 4)
        step = self.app.result_step
        self.assertEqual(step.pager.total, 1201)
        self.assertEqual(len(step.result_table.get_children()), 500)
        step.pager.move(1)
        self.assertEqual(step.result_table.get_children()[0], "501")
        step.pager.move(1)
        self.assertEqual(len(step.result_table.get_children()), 201)
        step.pager.filter.set("Nur Fehler")
        step.pager.refresh(reset=True)
        self.assertEqual(step.pager.total, 1)
        self.assertEqual(step.result_table.get_children(), ("1201",))
        self.assertEqual(step.page_rows["1201"]["parse_error"], "late error")
        self.assertIn("1201 Nachrichten", step.result_status.get())
        self.assertIsNone(self.app.processing_step.display.timer)

    def test_export_phase_remains_active_and_can_be_cancelled(self):
        self.prepare(create_sources(self.root))
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)

        def gated(*args):
            entered.set()
            if not release.wait(5):
                raise RuntimeError("export test timeout")
            return _write_output(*args)

        with patch("mailanalyst.exports.dispatch._write_output", side_effect=gated):
            self.app.processing_step._start_processing()
            self.wait_for(entered.is_set)
            step = self.app.processing_step
            self.wait_for(lambda: step.processing_status.get() == "Exportieren")
            self.assertEqual(str(step.processing_progress["mode"]), "indeterminate")
            self.wait_for(lambda: "2 Nachrichten gelesen" in step.display.clock.get())
            self.app.activity.cancel()
            release.set()
            self.wait_for(lambda: not self.app.jobs.busy)
        manifest = next((self.root / "output/runs").glob("*/manifest.json"))
        self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["status"], "cancelled")
        self.assertFalse((manifest.parent / "exports").exists())
        self.assertIsNone(step.display.timer)

    def test_many_progress_events_keep_latest_counter(self):
        self.wait_for(lambda: bool(self.app.system_check_results))
        received, completed = [], []

        def work(progress):
            for count in range(50000):
                progress(count + 1, 50000, Path("synthetic.eml"))
            return "done"

        self.app.jobs.submit(work, completed.append, self.errors.append, lambda *args: received.append(args))
        self.wait_for(lambda: bool(completed))
        self.assertEqual(received[-1][0], 50000)
        self.assertLess(len(received), 100)
        self.assertEqual(self.app.jobs._latest_progress, {})
