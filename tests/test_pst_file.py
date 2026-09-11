"""Optional real-file libpff integration test with a pinned public PST."""

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from mailanalyst.services import ProcessingOptions, process_sources
from mailanalyst.config import LOGGER
from tests.pst_fixture import (EXPECTED_DATE, EXPECTED_FOLDERS, EXPECTED_SUBJECT,
                               PST_FIXTURE_SHA256, require_fixture)


class PstFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configured = os.environ.get("MAILANALYST_PST_TEST_FILE")
        if not configured:
            raise unittest.SkipTest("MAILANALYST_PST_TEST_FILE is not set")
        try:
            import pypff  # noqa: F401
        except ImportError as exc:
            raise unittest.SkipTest("pypff is not installed") from exc
        cls.path = require_fixture(Path(configured))

    def test_libpff_file_workflow_cache_and_source_integrity(self):
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            try:
                target = Path(temporary) / "output"
                options = ProcessingOptions(
                    self.path, target, (self.path,), "Analysepaket",
                    "Ohne Outlook (libpff)", "Vollstaendige URLs", hash_check=True,
                )
                first = process_sources(options)
                first_run = Path(first.attrs["run_directory"])
                manifest_path = first_run / "manifest.json"
                first_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                export_path = first_run / "exports" / "emails.json"
                rows = json.loads(export_path.read_text(encoding="utf-8"))
                self.assertEqual(first_manifest["status"], "completed")
                self.assertEqual((first_manifest["messages"], first_manifest["parser_errors"]), (2, 0))
                self.assertEqual(first_manifest["quality_warnings"], 2)
                self.assertEqual({row["subject"] for row in rows}, {EXPECTED_SUBJECT})
                self.assertEqual({row["sent_at_utc"] for row in rows}, {EXPECTED_DATE})
                self.assertEqual({row["outlook_folder"] for row in rows}, EXPECTED_FOLDERS)
                self.assertEqual({row["pst_backend"] for row in rows}, {"libpff"})
                self.assertEqual({row["to_emails"] for row in rows}, {""})
                warning_path = first_run / "quality_warnings.jsonl"
                warnings = [json.loads(line) for line in warning_path.read_text(encoding="utf-8").splitlines()]
                self.assertEqual({item["code"] for item in warnings}, {"unresolved_email"})

                second = process_sources(options)
                second_run = Path(second.attrs["run_directory"])
                manifest_path = second_run / "manifest.json"
                second_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                self.assertEqual((second_manifest["cache_hits"], second_manifest["messages"]), (1, 2))
            finally:
                for handler in LOGGER.handlers[:]:
                    handler.close()
                    LOGGER.removeHandler(handler)
        self.assertEqual(require_fixture(self.path), self.path)
        after = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.assertEqual(before, PST_FIXTURE_SHA256)
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
