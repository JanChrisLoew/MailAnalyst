"""Real MSG binary parsing with synthetic content; no parser test doubles."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from mailanalyst.batch_pipeline import build_store
from mailanalyst.checks.preflight import check_file
from mailanalyst.config import LOGGER
from mailanalyst.hashing import file_signature
from mailanalyst.parsing.dispatch import parse_mail_file
from mailanalyst.services import ProcessingOptions, process_sources
from tests.msg_samples import CASES, create_msg_sources


class MsgFileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.close_logs)
        self.root = Path(self.temp.name)
        self.source = create_msg_sources(self.root)

    @staticmethod
    def close_logs():
        for handler in LOGGER.handlers[:]:
            handler.close()
            LOGGER.removeHandler(handler)

    def test_real_msg_fields_and_source_provenance(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                path = self.source / (case["name"] + ".msg")
                self.assertEqual(check_file(path).status, "ok")
                row, = parse_mail_file(path, file_signature(path), "Europe/Berlin")
                self.assertEqual(row["parse_status"], "ok", row["parse_error"])
                self.assertEqual(row["subject"], case["subject"])
                self.assertEqual(row["message_id"], f"<{case['name']}@example.test>")
                self.assertEqual(row["from_email"], "anna@example.test")
                self.assertEqual(row["to_emails"], "ben@example.test")
                self.assertEqual(row["cc_emails"], "carla@example.test")
                self.assertEqual(row["sent_at_utc"], case["date"])
                self.assertEqual(row["sent_datetime_de"], case["local"])
                self.assertIn(case.get("body", case.get("body_contains")), row["body_text_clean"])
                self.assertEqual(row["attachment_count"], int("attachment" in case))
                self.assertEqual(row["attachment_names"], case.get("attachment", ""))
                self.assertEqual(row["in_reply_to"], case.get("reply", ""))
                self.assertEqual(row["references"], case.get("reply", ""))
                self.assertEqual(row["source_file_path"], str(path.resolve()))
                self.assertEqual(len(row["file_sha256"]), 64)

    def test_real_msg_analysis_package_and_cache(self):
        options = ProcessingOptions(self.source, self.root / "output", tuple(self.source.glob("*.msg")),
                                    "Analysepaket", "Automatisch", "Vollständige URLs", hash_check=True)
        for expected_mode in ("parsed", "cache"):
            frame = process_sources(options)
            run = Path(frame.attrs["run_directory"])
            manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "completed")
            rows = json.loads((run / "exports/emails.json").read_text(encoding="utf-8"))
            parquet = pd.read_parquet(run / "exports/emails.parquet").to_dict("records")
            self.assertEqual(len(rows), len(CASES))
            self.assertEqual({r["message_id"] for r in rows}, {f"<{c['name']}@example.test>" for c in CASES})
            fields = ("message_id", "subject", "sent_at_utc", "body_text_clean", "attachment_names")
            self.assertEqual(sorted(tuple(r[f] for f in fields) for r in rows),
                             sorted(tuple(r[f] for f in fields) for r in parquet))
            audits = [json.loads(line) for line in (run / "sources.jsonl").read_text().splitlines()]
            self.assertEqual(len(audits), len(CASES))
            self.assertEqual({a["mode"] for a in audits}, {expected_mode})
            self.assertEqual({a["hash_status"] for a in audits}, {"verified_this_run"})

    def test_truncated_msg_yields_visible_error_and_can_be_replaced(self):
        path = self.source / "plain.msg"
        path.write_bytes(path.read_bytes()[:128])
        row, = parse_mail_file(path, file_signature(path), "Europe/Berlin")
        self.assertEqual(row["parse_status"], "error")
        self.assertTrue(row["parse_error"])
        self.assertEqual(row["source_file_path"], str(path.resolve()))
        path.unlink()  # Parser released the damaged container as well.

    def test_previous_parser_revision_forces_real_msg_reimport(self):
        path = self.source / "plain.msg"
        cache = self.root / "cache.sqlite3"
        with patch("mailanalyst.cache.PARSER_VERSION", 1):
            old = build_store(path, cache, self.root / "old.sqlite3")
            old.close()
        current = build_store(path, cache, self.root / "current.sqlite3")
        try:
            self.assertEqual(next(current.audits())["mode"], "parsed")
            self.assertEqual(next(current.records())["sent_at_utc"], CASES[0]["date"])
        finally:
            current.close()
