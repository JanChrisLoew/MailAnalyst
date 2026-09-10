"""Inventory and content binding with actual synthetic files."""

import json
import os
from pathlib import Path
import tempfile
import unittest

from mailanalyst.config import LOGGER
from mailanalyst.checks.preflight import run_preflight
from mailanalyst.services import ProcessingOptions, check_sources, process_sources
from tests.samples import create_sources


class PreflightBindingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.addCleanup(self.close_logs)
        self.root = Path(temp.name)
        self.source = create_sources(self.root)

    @staticmethod
    def close_logs():
        for handler in LOGGER.handlers[:]:
            handler.close()
            LOGGER.removeHandler(handler)

    def options(self, rows):
        return ProcessingOptions(self.source, self.root / "output", tuple(Path(r.path) for r in rows if r.include),
                                 "JSON", "Automatisch", "Vollständige URLs", preflight=tuple(rows))

    def test_inventory_includes_empty_ignored_and_excludes_target_subtree(self):
        (self.source / "empty.txt").write_bytes(b"")
        target = self.source / "output"
        target.mkdir()
        (target / "old.eml").write_bytes(b"not an input")
        rows = check_sources(self.source, target)
        self.assertEqual(len(rows), 4)
        self.assertEqual(sum(r.status == "ignored" for r in rows), 2)
        self.assertEqual(sum(r.include for r in rows), 2)
        self.assertFalse(any("old.eml" in r.path for r in rows))

    def test_same_size_and_mtime_mutation_rejects_before_parsing(self):
        rows = run_preflight(self.source)
        path = self.source / "first.eml"
        before = path.stat()
        data = path.read_bytes()
        self.assertIn(b"Freigabe", data)
        path.write_bytes(data.replace(b"Freigabe", b"Geaendrt"))
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual(path.stat().st_size, before.st_size)
        with self.assertRaisesRegex(RuntimeError, "seit der Vorpruefung"):
            process_sources(self.options(rows))
        manifest = next((self.root / "output/runs").glob("*/manifest.json"))
        self.assertEqual(json.loads(manifest.read_text())["status"], "failed")
        self.assertFalse((manifest.parent / "exports").exists())

    def test_bound_run_reports_selection_and_verified_cache(self):
        rows = run_preflight(self.source)
        options = self.options(rows)
        for mode in ("parsed", "cache"):
            result = process_sources(options)
            run = Path(result.attrs["run_directory"])
            report = json.loads((run / "preflight_report.json").read_text())
            self.assertEqual(len(report), 3)
            self.assertEqual(sum(r["include"] for r in report), 2)
            audits = [json.loads(line) for line in (run / "sources.jsonl").read_text().splitlines()]
            self.assertEqual({r["mode"] for r in audits}, {mode})
            self.assertEqual({r["hash_status"] for r in audits}, {"verified_this_run"})
            self.assertTrue((run / "system_check_report.json").is_file())

    def test_unchecked_selection_and_ignored_file_cannot_be_imported(self):
        rows = run_preflight(self.source)
        options = self.options(rows[:1])
        from dataclasses import replace
        with self.assertRaisesRegex(RuntimeError, "nicht vollstaendig"):
            process_sources(replace(options, paths=(self.source / "second.eml",)))
        with self.assertRaisesRegex(RuntimeError, "Nicht unterstuetzte"):
            process_sources(replace(options, paths=(self.source / "ignored.txt",), preflight=tuple(rows)))

    def test_archive_fingerprint_is_checked_before_backend_opens_file(self):
        from mailanalyst.batch_pipeline import build_store
        from mailanalyst.checks.preflight import check_file
        from unittest.mock import patch
        path = self.root / "synthetic.pst"
        path.write_bytes(b"!BDN synthetic placeholder")
        row = check_file(path)
        path.write_bytes(b"!BDN changed placeholder")
        guard = {row.path: (row.size, row.modified_at_ns, row.sha256)}
        with patch("mailanalyst.batch_sources.iter_mail_file") as parser:
            with self.assertRaisesRegex(RuntimeError, "seit der Vorpruefung"):
                build_store(path, self.root / "cache.sqlite3", self.root / "work.sqlite3",
                            pst_backend="libpff", preflight=guard)
            parser.assert_not_called()
