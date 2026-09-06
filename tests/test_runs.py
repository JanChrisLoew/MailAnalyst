"""Failure injection and independently readable published packages."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mailanalyst.config import LOGGER
from mailanalyst.exports.dispatch import write_output
from mailanalyst.exports.validation import validate_dataset
from mailanalyst.hashing import sha256_file
from mailanalyst.services import ProcessingOptions, process_sources
from tests.samples import create_sources


class RunTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.addCleanup(self.close_logs)
        self.root = Path(temp.name)
        self.source = create_sources(self.root)
        self.target = self.root / "output"
        self.options = ProcessingOptions(self.source, self.target, tuple(sorted(self.source.glob("*.eml"))),
                                         "Analysepaket", "Automatisch", "Vollstaendige URLs", hash_check=True)

    @staticmethod
    def close_logs():
        for handler in LOGGER.handlers[:]:
            handler.close()
            LOGGER.removeHandler(handler)

    def test_repeat_runs_are_separate_and_portable(self):
        first = process_sources(self.options)
        original = Path(first.attrs["run_directory"])
        before = (original / "exports/emails.json").read_bytes()
        second = process_sources(self.options)
        current = Path(second.attrs["run_directory"])
        self.assertNotEqual(current, original)
        self.assertEqual((original / "exports/emails.json").read_bytes(), before)
        manifest = json.loads((current / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "completed")
        self.assertEqual(manifest["cache_hits"], 2)
        for output in manifest["outputs"]:
            self.assertEqual(sha256_file(current / output["path"]), output["sha256"])
        copied = self.root / "copied"
        shutil.copytree(current / "exports", copied)
        validate_dataset(copied / "mail_workspace", 2)
        self.assertFalse((current / ".pending").exists())

    def test_export_failure_leaves_failed_run_and_previous_success(self):
        first = process_sources(self.options)
        original = Path(first.attrs["run_directory"])
        with patch("mailanalyst.exports.profiles.write_output", side_effect=OSError("synthetic disk failure")):
            with self.assertRaisesRegex(RuntimeError, "synthetic disk failure"):
                process_sources(self.options)
        manifests = [json.loads(path.read_text(encoding="utf-8"))
                     for path in (self.target / "runs").glob("*/manifest.json")]
        self.assertEqual(sorted(item["status"] for item in manifests), ["completed", "failed"])
        self.assertTrue((original / "exports/emails.json").is_file())
        failed = next(item for item in manifests if item["status"] == "failed")
        self.assertFalse((self.target / "runs" / failed["run_id"] / "exports").exists())

    def test_validation_failure_preserves_existing_file(self):
        frame = process_sources(self.options)
        output = self.root / "existing.json"
        output.write_text("previous", encoding="utf-8")
        with patch("mailanalyst.exports.dispatch.validate_output", side_effect=ValueError("invalid export")):
            with self.assertRaisesRegex(ValueError, "invalid export"):
                write_output(frame, output)
        self.assertEqual(output.read_text(encoding="utf-8"), "previous")
        self.assertEqual(list(self.root.glob(".pending-*")), [])

    def test_empty_selection_has_valid_empty_package(self):
        from dataclasses import replace
        frame = process_sources(replace(self.options, paths=()))
        run = Path(frame.attrs["run_directory"])
        self.assertEqual(len(frame), 0)
        validate_dataset(run / "exports/mail_workspace", 0)

    def test_legacy_directory_keeps_previous_content(self):
        from mailanalyst.legacy_outputs import publish_copy
        source = self.root / "new-dataset"
        source.mkdir()
        (source / "new.md").write_text("new", encoding="utf-8")
        target = self.root / "legacy"
        target.mkdir()
        (target / "old.md").write_text("old", encoding="utf-8")
        publish_copy(source, target)
        self.assertEqual([path.name for path in target.iterdir()], ["new.md"])
        previous = list(self.root.glob(".previous-*/old.md"))
        self.assertEqual(len(previous), 1)
        self.assertEqual(previous[0].read_text(encoding="utf-8"), "old")

    def test_interrupted_run_is_not_complete(self):
        from mailanalyst.runs import Run
        run = Run(self.target, {})
        manifest = json.loads((run.root / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "running")
        self.assertIsNone(manifest["finished_at"])
        self.assertFalse((run.root / "exports").exists())

    def test_parser_errors_are_published_and_logged_explicitly(self):
        from mailanalyst.parsing.dispatch import parse_mail_file

        def error_rows(*args):
            rows = parse_mail_file(*args)
            for row in rows:
                row.update(parse_status="error", parse_error="synthetic parser error")
            return rows

        with patch("mailanalyst.source_processing.parse_mail_file", side_effect=error_rows):
            frame = process_sources(self.options)
        run = Path(frame.attrs["run_directory"])
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "completed_with_errors")
        self.assertEqual(manifest["parser_errors"], 2)
        self.assertIn("synthetic parser error", (run / "parse_log.txt").read_text(encoding="utf-8"))
