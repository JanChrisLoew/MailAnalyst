"""Synthetic corruption, invalidation, and source mutation coverage."""

import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from mailanalyst.cache import load_cache, sqlite_path
from mailanalyst.pipeline import build_dataframe
from mailanalyst.source_processing import process_source
from mailanalyst.parsing.dispatch import parse_mail_file
from tests.samples import create_sources


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = create_sources(self.root)
        self.cache = self.root / "cache.pkl"

    def build(self, **kwargs):
        return build_dataframe(self.source, self.cache, **kwargs)

    def test_pickle_is_never_loaded_and_corrupt_sqlite_is_rebuilt(self):
        self.cache.write_bytes(b"legacy pickle must remain untouched")
        with patch("pandas.read_pickle", side_effect=AssertionError("Unsafe cache load")):
            self.build()
            sqlite_path(self.cache).write_bytes(b"broken sqlite")
            frame = self.build()
        self.assertEqual(len(frame), 2)
        self.assertTrue(all(row["mode"] == "parsed" for row in frame.attrs["sources"]))
        self.assertEqual(self.cache.read_bytes(), b"legacy pickle must remain untouched")

    def test_schema_and_timezone_invalidate_cache(self):
        first = self.build()
        berlin = first.iloc[0].sent_datetime_de
        utc = self.build(timezone_name="UTC")
        self.assertNotEqual(berlin, utc.iloc[0].sent_datetime_de)
        self.assertTrue(all(row["mode"] == "parsed" for row in utc.attrs["sources"]))
        with closing(sqlite3.connect(sqlite_path(self.cache))) as connection:
            connection.execute("PRAGMA user_version=999")
            connection.commit()
        self.assertEqual(load_cache(self.cache, False), {})
        self.assertEqual(len(self.build()), 2)

    def test_invalid_payload_rebuilds(self):
        self.build()
        with closing(sqlite3.connect(sqlite_path(self.cache))) as connection:
            connection.execute("UPDATE sources SET payload=?", (json.dumps({"rows": [42]}),))
            connection.commit()
        self.assertEqual(load_cache(self.cache, False), {})
        self.assertEqual(len(self.build()), 2)

    def test_hash_detects_same_size_same_mtime_change(self):
        first = self.build()
        path = self.source / "first.eml"
        stat = path.stat()
        path.write_bytes(path.read_bytes().replace(b"Freigabe erfolgt.", b"Freigabe offen!!!"))
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        fast = self.build()
        self.assertEqual(fast.iloc[0].file_sha256, first.iloc[0].file_sha256)
        self.assertEqual(fast.attrs["sources"][0]["hash_status"], "reused_unverified")
        self.assertIsNone(fast.attrs["sources"][0]["hash_verified_at"])
        strict = self.build(hash_check=True)
        self.assertNotEqual(strict.iloc[0].file_sha256, first.iloc[0].file_sha256)
        self.assertEqual(strict.attrs["sources"][0]["hash_status"], "verified_this_run")

    def test_source_mutation_does_not_replace_previous_cache(self):
        self.build()
        previous = sqlite_path(self.cache).read_bytes()

        def mutate(path, *args):
            rows = parse_mail_file(path, *args)
            path.write_bytes(path.read_bytes() + b"changed")
            return rows

        with patch("mailanalyst.source_processing.parse_mail_file", side_effect=mutate):
            with self.assertRaisesRegex(RuntimeError, "Quelle.*geaendert"):
                self.build(refresh=True)
        self.assertEqual(sqlite_path(self.cache).read_bytes(), previous)

    def test_auto_backend_change_and_empty_pst_cache(self):
        path = self.root / "empty.pst"
        path.write_bytes(b"synthetic pst double")
        with patch("mailanalyst.source_processing.resolve_pst_backend", return_value="libpff"), \
             patch("mailanalyst.source_processing.parse_mail_file", return_value=[]) as parser:
            _, entry, audit = process_source(path, {}, False, "UTC", "auto")
            cache = {str(path.resolve()): entry}
            _, _, second = process_source(path, cache, True, "UTC", "auto")
            self.assertEqual(second["mode"], "cache")
            self.assertEqual(parser.call_count, 1)
        with patch("mailanalyst.source_processing.resolve_pst_backend", return_value="outlook"), \
             patch("mailanalyst.source_processing.parse_mail_file", return_value=[]) as parser:
            _, _, third = process_source(path, cache, True, "UTC", "auto")
            self.assertEqual(third["mode"], "parsed")
            self.assertEqual(parser.call_count, 1)

    def test_failed_cache_replace_keeps_previous_database(self):
        self.build()
        previous = sqlite_path(self.cache).read_bytes()
        with patch("mailanalyst.cache.os.replace", side_effect=OSError("cache write failed")):
            with self.assertRaisesRegex(OSError, "cache write failed"):
                self.build(refresh=True)
        self.assertEqual(sqlite_path(self.cache).read_bytes(), previous)
        self.assertEqual(list(self.root.glob("cache-*.sqlite3")), [])
