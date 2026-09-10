"""Actual mixed file parsing and exports with explicit synthetic expectations."""

import csv
import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

import pandas as pd
from openpyxl import load_workbook

from mailanalyst.checks.preflight import check_file, run_preflight
from mailanalyst.config import LOGGER
from mailanalyst.discovery import discover_mail_files
from mailanalyst.exports.dispatch import write_output
from mailanalyst.hashing import file_signature
from mailanalyst.parsing.dispatch import parse_mail_file
from mailanalyst.review_store import read_review
from mailanalyst.services import ProcessingOptions, process_sources
from tests.corpus_samples import create_corpus


class MailCorpusTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.addCleanup(self.close_logs)
        self.root = Path(temp.name) / "corpus"
        self.expected = create_corpus(self.root)
        self.source = self.root / "input"

    @staticmethod
    def close_logs():
        for handler in LOGGER.handlers[:]:
            handler.close()
            LOGGER.removeHandler(handler)

    def test_all_real_msg_and_eml_variants(self):
        paths = discover_mail_files(self.source)
        self.assertEqual(len(paths), 22)
        self.assertEqual({r.status for r in run_preflight(self.source)}, {"ok"})
        for path in paths:
            with self.subTest(path=path.name, extension=path.suffix):
                expected = self.expected[path.relative_to(self.source).as_posix()]
                row, = parse_mail_file(path, file_signature(path), "Europe/Berlin")
                self.assertEqual(row["parse_status"], "ok", row["parse_error"])
                for field in ("message_id", "subject", "sent_at_utc", "attachment_names", "attachment_count"):
                    self.assertEqual(row[field], expected[field], field)
                self.assertIn(expected["body_contains"], row["body_text_clean"])
                self.assertEqual(row["from_email"], "anna@example.test")
                self.assertIn("ben@example.test", row["to_emails"])
                if path.suffix == ".eml":
                    self.assertIn("dora@example.test", row["to_emails"])
                    self.assertEqual(row["bcc_emails"], "erik@example.test")
                    self.assertEqual(row["reply_to_emails"], "antwort@example.test")

    def test_negative_probes_are_rejected_or_ignored_without_outlook(self):
        for path in (self.root / "negative").iterdir():
            with self.subTest(path=path.name):
                expected = "error" if path.suffix in {".msg", ".eml", ".pst"} else "ignored"
                self.assertEqual(check_file(path).status, expected)
                self.assertFalse(check_file(path).include)
        # Folder discovery still excludes unsupported files (CHECK-02 remains open).
        self.assertEqual(len(discover_mail_files(self.root / "negative")), 5)

    def test_mixed_package_and_additional_export_formats(self):
        options = ProcessingOptions(self.source, self.root / "output", tuple(discover_mail_files(self.source)),
                                    "Analysepaket", "Automatisch", "Vollständige URLs", hash_check=True)
        frame = process_sources(options)
        run = Path(frame.attrs["run_directory"])
        rows = json.loads((run / "exports/emails.json").read_text(encoding="utf-8"))
        parquet = pd.read_parquet(run / "exports/emails.parquet")
        self.assertEqual(len(rows), 22)
        self.assertEqual(set(parquet.message_id), {e["message_id"] for e in self.expected.values()})
        expected = {e["message_id"]: e for e in self.expected.values()}
        for row in rows:
            for field in ("subject", "sent_at_utc", "attachment_names", "attachment_count"):
                self.assertEqual(row[field], expected[row["message_id"]][field])
        for extension in ("csv", "xlsx", "xml", "md"):
            write_output(frame, self.root / ("export." + extension))
        with (self.root / "export.csv").open(encoding="utf-8-sig", newline="") as stream:
            csv_rows = list(csv.DictReader(stream))
        self.assertEqual(len(csv_rows), 22)
        self.assertEqual(sum(r["subject"] == "'=1+1" for r in csv_rows), 2)
        book = load_workbook(self.root / "export.xlsx", read_only=True)
        try:
            records = list(book.active.rows)
            self.assertEqual(len(records), 23)
            self.assertFalse(any(c.data_type == "f" for row in records for c in row))
        finally:
            book.close()
        self.assertEqual(len(ElementTree.parse(self.root / "export.xml").getroot()), 22)
        self.assertIn("Langer Text", (self.root / "export.md").read_text(encoding="utf-8"))

    def test_550_messages_span_review_pages_and_cache(self):
        root = self.root / "bulk"
        expected = create_corpus(root, repeat=25)
        source = root / "input"
        options = ProcessingOptions(source, root / "output", tuple(discover_mail_files(source)),
                                    "JSON", "Automatisch", "Vollständige URLs")
        for mode in ("parsed", "cache"):
            frame = process_sources(options)
            run = Path(frame.attrs["run_directory"])
            rows = json.loads((run / "exports/emails.json").read_text(encoding="utf-8"))
            self.assertEqual(len(rows), 550)
            self.assertEqual({r["message_id"] for r in rows}, {e["message_id"] for e in expected.values()})
            self.assertEqual({r["parse_status"] for r in rows}, {"ok"})
            first, total = read_review(run / "exports/review.sqlite3")
            second, _ = read_review(run / "exports/review.sqlite3", offset=500)
            self.assertEqual((len(first), len(second), total), (500, 50, 550))
            self.assertFalse({seq for seq, _ in first} & {seq for seq, _ in second})
            audits = [json.loads(line) for line in (run / "sources.jsonl").read_text().splitlines()]
            self.assertEqual(len(audits), 550)
            self.assertEqual({a["mode"] for a in audits}, {mode})
