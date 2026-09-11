"""PST adapters with lazy testdoubles, resource cleanup and archive integrity."""

import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from mailanalyst.batch_pipeline import build_store
from mailanalyst.cancellation import Cancellation, Cancelled
from mailanalyst.hashing import file_signature
from mailanalyst.parsing.pst_libpff import iter_pst_libpff
from mailanalyst.parsing.pst_outlook import iter_pst_outlook


class PstStreamingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / "synthetic.pst"
        self.path.write_bytes(b"synthetic placeholder; not a real PST")
        self.signature = file_signature(self.path, include_hash=True)

    def test_libpff_is_lazy_and_closes_on_generator_close(self):
        folder = types.SimpleNamespace(name="Synthetic", number_of_sub_messages=1000, number_of_sub_folders=0)
        folder.get_sub_message = Mock(side_effect=lambda i: types.SimpleNamespace(identifier=i, subject=f"Mail {i}"))
        archive = types.SimpleNamespace(get_root_folder=lambda: folder, close=Mock())
        pypff = types.SimpleNamespace(open_file_object=Mock(return_value=archive))
        with patch.dict("sys.modules", {"pypff": pypff}):
            iterator = iter_pst_libpff(self.path, self.signature, "Europe/Berlin")
            self.assertEqual(next(iterator)["subject"], "Mail 0")
            source_stream = pypff.open_file_object.call_args.args[0]
            self.assertFalse(source_stream.closed)
            self.assertEqual(folder.get_sub_message.call_count, 1)
            iterator.close()
            archive.close.assert_called_once()
            self.assertTrue(source_stream.closed)

    def test_outlook_generator_closes_only_its_own_store(self):
        items = types.SimpleNamespace(Count=1000, Item=Mock(return_value=types.SimpleNamespace(Class=43)))
        folder = types.SimpleNamespace(Name="Synthetic", Items=items, Folders=types.SimpleNamespace(Count=0))
        store = types.SimpleNamespace(FilePath=str(self.path), GetRootFolder=lambda: folder)
        for existing in (False, True):
            namespace = types.SimpleNamespace(Stores=[store] if existing else [], RemoveStore=Mock())
            namespace.AddStoreEx = Mock(side_effect=lambda *_: namespace.Stores.append(store))
            client = types.ModuleType("win32com.client")
            client.Dispatch = lambda _: types.SimpleNamespace(GetNamespace=lambda _: namespace)
            win32com = types.ModuleType("win32com")
            win32com.client = client
            com = types.SimpleNamespace(CoInitialize=Mock(), CoUninitialize=Mock())
            with patch.dict("sys.modules", {"win32com": win32com, "win32com.client": client, "pythoncom": com}):
                iterator = iter_pst_outlook(self.path, self.signature, "Europe/Berlin")
                self.assertEqual(next(iterator)["pst_backend"], "outlook")
                iterator.close()
            self.assertEqual(namespace.RemoveStore.call_count, 0 if existing else 1)
            com.CoUninitialize.assert_called_once()

    def test_archive_batches_cache_cancellation_and_mutation(self):
        closed = []

        def rows(path, signature, *_):
            try:
                for i in range(1201):
                    yield {**signature.__dict__, "source_file_path": signature.key, "cache_schema_version": 7,
                           "parse_status": "ok", "message_id": f"<{i}@example.test>"}
            finally:
                closed.append(True)

        cache = self.root / "cache.sqlite3"
        with patch("mailanalyst.batch_sources.iter_mail_file", side_effect=rows) as parser:
            first = build_store(self.path, cache, self.root / "first.sqlite3", pst_backend="libpff")
            self.assertEqual(first.max_batch_rows, 500)
            self.assertEqual(len(first), 1201)
            first.close()
            second = build_store(self.path, cache, self.root / "second.sqlite3", pst_backend="libpff")
            self.assertEqual(next(second.audits())["mode"], "cache")
            second.close()
            self.assertEqual(parser.call_count, 1)
            previous = cache.read_bytes()
            token = Cancellation()
            with self.assertRaises(Cancelled):
                build_store(self.path, cache, self.root / "cancel.sqlite3", refresh=True, cancel=token,
                            pst_backend="libpff", progress_callback=lambda *_: token.request())
            self.assertEqual(cache.read_bytes(), previous)
        self.assertEqual(len(closed), 2)

        def mutate(*args):
            yield from rows(*args)
            self.path.write_bytes(b"changed synthetic source")

        with patch("mailanalyst.batch_sources.iter_mail_file", side_effect=mutate), self.assertRaisesRegex(RuntimeError, "geaendert"):
            build_store(self.path, cache, self.root / "mutated.sqlite3", refresh=True, pst_backend="libpff")
        self.assertEqual(cache.read_bytes(), previous)

    def test_dispatch_preserves_partial_archive_with_error_row(self):
        from mailanalyst.parsing.dispatch import iter_mail_file

        def broken(*_):
            yield {"source_file_path": self.signature.key, "parse_status": "ok"}
            raise ValueError("synthetic traversal failure")

        with patch("mailanalyst.parsing.dispatch.iter_pst_libpff", side_effect=broken):
            rows = list(iter_mail_file(self.path, self.signature, "Europe/Berlin", "libpff"))
        self.assertEqual([row["parse_status"] for row in rows], ["ok", "error"])
        self.assertEqual(rows[1]["source_file_path"], self.signature.key)
        self.assertIn("synthetic traversal failure", rows[1]["parse_error"])
