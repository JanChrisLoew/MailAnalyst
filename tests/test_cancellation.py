"""Cancellation checkpoints around cache writes and package publication."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mailanalyst.cancellation import Cancellation, Cancelled
from mailanalyst.config import LOGGER
from mailanalyst.hashing import sha256_file
from mailanalyst.pipeline import build_dataframe
from mailanalyst.services import ProcessingOptions, process_sources
from mailanalyst.exports.profiles import write_output
from tests.samples import create_sources


class CancellationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.addCleanup(self.close_logs)
        self.root = Path(temp.name)
        self.source = create_sources(self.root)
        self.cache = self.root / "cache.sqlite3"
        self.token = Cancellation()

    @staticmethod
    def close_logs():
        for handler in LOGGER.handlers[:]:
            handler.close()
            LOGGER.removeHandler(handler)

    def test_cancel_on_progress_preserves_cache(self):
        build_dataframe(self.source, self.cache)
        before = self.cache.read_bytes()
        with self.assertRaises(Cancelled):
            build_dataframe(self.source, self.cache, refresh=True, workers=1, cancel=self.token,
                            progress_callback=lambda *args: self.token.request())
        self.assertEqual(self.cache.read_bytes(), before)

    def test_cancel_between_exports_never_publishes_partial_package(self):
        target = self.root / "output"
        options = ProcessingOptions(self.source, target, tuple(self.source.glob("*.eml")),
                                    "Analysepaket", "Automatisch", "Kompakte URLs")
        written = []

        def cancel_after_write(*args):
            write_output(*args)
            written.append(args[1])
            self.token.request()

        with patch("mailanalyst.exports.profiles.write_output", side_effect=cancel_after_write):
            with self.assertRaises(Cancelled):
                process_sources(options, cancel=self.token)
        manifest = next((target / "runs").glob("*/manifest.json"))
        self.assertEqual(len(written), 1)
        self.assertTrue(written[0].exists())
        self.assertFalse((manifest.parent / "exports").exists())
        self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["status"], "cancelled")

    def test_cancel_before_commit_wins_and_after_commit_is_refused(self):
        self.assertTrue(self.token.request())
        with self.assertRaises(Cancelled):
            self.token.begin_commit()
        token = Cancellation()
        token.begin_commit()
        self.assertFalse(token.request())
        token.check()

    def test_hash_loop_checks_cancellation(self):
        self.token.request()
        with self.assertRaises(Cancelled):
            sha256_file(self.source / "first.eml", chunk_size=16, cancel=self.token)
