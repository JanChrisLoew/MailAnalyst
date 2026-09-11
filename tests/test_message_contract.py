"""Executable message contract and hardened text-export behavior."""

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from mailanalyst.exports.dispatch import write_output
from mailanalyst.message_schema import MESSAGE_SCHEMA_VERSION, assess_message
from mailanalyst.record_store import RecordStore
from mailanalyst.runs import Run


def row(**values):
    base = {"source_path": "synthetic.eml", "source_file_path": "synthetic.eml",
            "parse_status": "ok", "parse_error": "", "sent_at_utc": "2026-09-01T10:00:00+00:00",
            "from_name": "Name", "from_email": "name@example.test", "to": "Recipient",
            "to_emails": "", "body_text_clean": "Text", "body_html": "",
            "attachment_count": 0, "has_attachments": False}
    return {**base, **values}


class MessageContractTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_contract_rejects_missing_reference_wrong_type_and_non_utc_date(self):
        cases = (
            ({**row(), "source_path": ""}, "Pflichtbezug source_path"),
            ({**row(), "attachment_count": "1"}, "attachment_count"),
            ({**row(), "sent_at_utc": "2026-09-01T10:00:00"}, "muss UTC"),
        )
        for message, expected in cases:
            with self.subTest(expected=expected), self.assertRaisesRegex(ValueError, expected):
                assess_message(message)

    def test_stable_warnings_distinguish_unresolved_names_from_smtp_addresses(self):
        warnings = assess_message(row())
        self.assertEqual([(item["code"], item["field"]) for item in warnings],
                         [("unresolved_email", "to_emails")])
        self.assertEqual(assess_message(row(to="Recipient <r@example.test>",
                                            to_emails="r@example.test")), [])

    def test_embedded_message_warning_is_stable(self):
        warnings = assess_message(row(to="", embedded_attachment_count=1,
                                      attachment_count=1, has_attachments=True))
        self.assertEqual([(item["code"], item["field"]) for item in warnings], [
            ("embedded_message_not_extracted", "embedded_attachment_count"),
        ])

    def test_run_manifest_and_jsonl_record_quality_warnings(self):
        store = RecordStore(self.root / "work.sqlite3")
        self.addCleanup(store.close)
        store.append("synthetic.eml", [row()])
        run = Run(self.root, {})
        run.record_store(store)
        manifest = json.loads((run.root / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["versions"]["message_schema"], MESSAGE_SCHEMA_VERSION)
        self.assertEqual(manifest["quality_warning_messages"], 1)
        warning = json.loads((run.root / "quality_warnings.jsonl").read_text(encoding="utf-8"))
        self.assertEqual((warning["message_number"], warning["code"]), (1, "unresolved_email"))

    def test_markdown_quotes_body_and_escapes_mail_controlled_structure(self):
        store = RecordStore(self.root / "markdown.sqlite3")
        self.addCleanup(store.close)
        store.append("synthetic.eml", [row(subject="# Heading <tag>", from_email="a|b@example.test",
                                                to="", body_text_clean="---\n# injected\n<a id='bad'>")])
        path = self.root / "emails.md"
        write_output(store, path)
        text = path.read_text(encoding="utf-8")
        self.assertIn(r"## 1. \# Heading &lt;tag&gt;", text)
        self.assertIn(r"a\|b@example\.test", text)
        self.assertIn("\n> ---\n> # injected\n> &lt;a id='bad'&gt;\n", text)

    def test_xml_preserves_valid_supplementary_unicode_and_removes_controls(self):
        store = RecordStore(self.root / "xml.sqlite3")
        self.addCleanup(store.close)
        store.append("synthetic.eml", [row(subject="Valid 😀 invalid \x01")])
        path = self.root / "emails.xml"
        write_output(store, path)
        text = path.read_text(encoding="utf-8")
        self.assertIn("Valid 😀 invalid ", text)
        self.assertNotIn("\x01", text)
        dataframe_path = self.root / "dataframe.xml"
        write_output(pd.DataFrame([{"subject": "Valid 😀 invalid \x01"}]), dataframe_path)
        dataframe_text = dataframe_path.read_text(encoding="utf-8")
        self.assertIn("Valid 😀 invalid ", dataframe_text)
        self.assertNotIn("\x01", dataframe_text)


if __name__ == "__main__":
    unittest.main()
