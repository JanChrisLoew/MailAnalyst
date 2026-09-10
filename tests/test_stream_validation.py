"""Malformed and large records are validated without whole-file reads."""

import io
import json
import tempfile
import unittest
from pathlib import Path

from mailanalyst.exports.json_stream import records
from mailanalyst.exports.validation import validate_dataset, validate_output


class StreamValidationTests(unittest.TestCase):
    def test_json_boundaries_and_invalid_syntax(self):
        row = {"text": "Ã¼\n\"" * 100000}
        self.assertEqual(list(records(io.StringIO(json.dumps([row, {}])))), [row, {}])
        self.assertEqual(list(records(io.StringIO(" [] "))), [])
        for value in ("", "{}", "[", "[{}", "[{},]", "[{} {}]", "[1]", "[]junk"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                list(records(io.StringIO(value)))

    def test_missing_anchor_path_escape_and_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "index.csv").write_text("anchor\nx\n", encoding="utf-8")
            (root / "month.md").write_text('<a id="x"></a>\n', encoding="utf-8")
            index = root / "index.jsonl"
            for name, anchor, succeeds in (("month.md", "x", True), ("month.md", "y", False),
                                           ("../outside.md", "x", False)):
                index.write_text(json.dumps({"markdown_file": name, "anchor": anchor}) + "\n", encoding="utf-8")
                if succeeds:
                    validate_dataset(root, 1)
                else:
                    with self.assertRaises(ValueError):
                        validate_dataset(root, 1)
            (root / "export.json").write_text("[{}]", encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_output(root / "export.json", 2)

    def test_csv_accepts_long_mail_bodies(self):
        import csv
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "long.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["body"])
                writer.writerow(["synthetic\n" * 30000])
            validate_output(path, 1)
