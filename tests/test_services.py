"""Regression coverage for GUI profiles and launch-directory independence."""

import json
import logging
import os
import tempfile
import unittest
from pathlib import Path

from mailanalyst.config import LOGGER
from mailanalyst.services import ProcessingOptions, process_sources
from tests.samples import create_sources


class ServiceTests(unittest.TestCase):
    def test_all_profiles_keep_cache_and_exports_in_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = create_sources(root)
            foreign = root / "unrelated-launch-directory"
            foreign.mkdir()
            original_cwd = Path.cwd()
            os.chdir(foreign)
            try:
                for profile, expected in (
                    ("Analysepaket", "emails.parquet"), ("Parquet", "emails.parquet"),
                    ("CSV", "emails.csv"), ("JSON", "emails.json"), ("Markdown", "emails.md"),
                    ("Markdown-Monatsordner", "mail_workspace/index.jsonl"),
                ):
                    with self.subTest(profile=profile):
                        target = root / profile
                        options = ProcessingOptions(source, target, tuple(sorted(source.glob("*.eml"))),
                                                    profile, "Automatisch", "Kompakte URLs", hash_check=True)
                        frame = process_sources(options)
                        self.assertEqual(len(frame), 2)
                        self.assertTrue((target / expected).is_file())
                        self.assertTrue((target / ".mailanalyst_cache/mail_metadata.pkl").is_file())
                        saved = json.loads((target / "processing_options.json").read_text(encoding="utf-8"))
                        self.assertEqual(saved["output"], str(target.resolve()))
                        events = []
                        previous_files = [handler for handler in LOGGER.handlers if isinstance(handler, logging.FileHandler)]
                        process_sources(options, lambda *event: events.append(event))
                        self.assertTrue(all(handler.stream is None for handler in previous_files))
                        self.assertEqual([event[3] for event in events], ["cache", "cache"])
                        self.close_logs()
                self.assertEqual(list(foreign.iterdir()), [])
            finally:
                os.chdir(original_cwd)
                self.close_logs()

    @staticmethod
    def close_logs():
        for handler in LOGGER.handlers[:]:
            handler.close()
            LOGGER.removeHandler(handler)
