"""Portable result index and observable service phases."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from mailanalyst.record_store import RecordStore
from mailanalyst.review_store import write_review, read_review
from mailanalyst.services import ProcessingOptions, process_sources
from tests.samples import create_sources
import tests.test_services as service_tests


class ReviewProgressTests(unittest.TestCase):
    def test_index_is_portable_bounded_and_excludes_bodies(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = RecordStore(root / "work.sqlite3")
            try:
                store.append("synthetic", ({"source_file_path": "synthetic",
                                           "subject": str(i), "body_text": "private body",
                                           "source_path": f"synthetic::{i}", "parse_status": "error" if i == 999 else "ok",
                                           "parse_error": "synthetic error" if i == 999 else ""} for i in range(1001)))
                write_review(store, root / "review.sqlite3")
            finally:
                store.close()
            shutil.copyfile(root / "review.sqlite3", root / "copy.sqlite3")
            rows, total = read_review(root / "copy.sqlite3", 500)
            self.assertEqual((len(rows), total), (500, 1001))
            self.assertNotIn("body_text", rows[0][1])
            errors, count = read_review(root / "copy.sqlite3", status="error")
            self.assertEqual(count, 1)
            self.assertEqual(errors[0][1]["source_path"], "synthetic::999")
            with self.assertRaises(ValueError):
                read_review(root / "copy.sqlite3", limit=501)

    def test_service_reports_export_validation_and_finalization(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = create_sources(root)
            options = ProcessingOptions(source, root / "output", tuple(source.glob("*.eml")),
                                        "Analysepaket", "Automatisch", "Vollstaendige URLs")
            events = []
            try:
                frame = process_sources(options, phase_progress=events.append)
                phases = [event.phase for event in events]
                self.assertEqual(phases[0], "Quellen prüfen")
                self.assertIn("Nachrichten lesen", phases)
                self.assertIn("Exportieren", phases)
                self.assertIn("Ausgaben prüfen", phases)
                self.assertEqual(phases[-1], "Abschließen")
                self.assertEqual(events[-1].messages, 2)
                run = Path(frame.attrs["run_directory"])
                manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
                self.assertIn("exports/review.sqlite3", [output["path"] for output in manifest["outputs"]])
            finally:
                service_tests.ServiceTests.close_logs()
