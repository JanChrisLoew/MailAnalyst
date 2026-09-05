"""Check extracted adapter wiring with test doubles, not real PST/MSG archives."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from mailanalyst.hashing import file_signature
from mailanalyst.parsing.dispatch import parse_mail_file, parse_pst


class ImporterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "synthetic.msg"
        self.path.write_bytes(b"synthetic adapter input")

    def test_msg_adapter_uses_helpers_and_closes_message(self):
        message = SimpleNamespace(
            sender="Bau <bau@example.test>", to="Pruefung <pruefung@example.test>",
            date="Tue, 01 Sep 2026 12:00:00 +0200", subject="Freigabe", body="",
            htmlBody=b"<p>Freigabe erfolgt.</p>", attachments=[SimpleNamespace(longFilename="beleg.txt")],
            headerDict={"Message-ID": "<msg@example.test>"}, close=Mock(),
        )
        with patch.dict("sys.modules", {"extract_msg": SimpleNamespace(openMsg=Mock(return_value=message))}):
            row = parse_mail_file(self.path, file_signature(self.path), "Europe/Berlin")[0]
        self.assertEqual(row["parse_status"], "ok")
        self.assertEqual(row["from_email"], "bau@example.test")
        self.assertEqual(row["body_text_clean"], "Freigabe erfolgt.")
        self.assertEqual(row["attachment_names"], "beleg.txt")
        self.assertEqual(row["sent_date_de"], "01.09.2026")
        message.close.assert_called_once()

    def test_missing_msg_dependency_becomes_an_error_row(self):
        with patch.dict("sys.modules", {"extract_msg": None}):
            row = parse_mail_file(self.path, file_signature(self.path), "Europe/Berlin")[0]
        self.assertEqual(row["parse_status"], "error")
        self.assertIn("MSG-Unterstuetzung fehlt", row["parse_error"])
        self.assertEqual(row["source_file_path"], str(self.path.resolve()))
        self.assertEqual(len(row["file_sha256"]), 64)

    def test_auto_pst_dispatch_uses_available_backend(self):
        for available in (True, False):
            with self.subTest(libpff_available=available), \
                 patch.dict("sys.modules", {"pypff": SimpleNamespace() if available else None}), \
                 patch("mailanalyst.parsing.dispatch.parse_pst_libpff", return_value=[{"pst_backend": "libpff"}]) as libpff, \
                 patch("mailanalyst.parsing.dispatch.parse_pst_outlook", return_value=[{}]) as outlook:
                rows = parse_pst(self.path, file_signature(self.path), "Europe/Berlin", "auto")
                self.assertEqual(rows[0]["pst_backend"], "libpff" if available else "outlook")
                self.assertEqual(libpff.call_count, int(available))
                self.assertEqual(outlook.call_count, int(not available))
