import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from mailanalyst.pipeline import build_dataframe
from mailanalyst.exports.markdown import write_markdown_dataset
from mailanalyst.exports.dispatch import write_output
from tests.samples import create_sources, portable_frame


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = create_sources(self.root)
        self.cache = self.root / "cache.pkl"

    def build(self, **kwargs):
        return build_dataframe(self.source, self.cache, **kwargs)

    def test_fields_and_cache_roundtrip(self):
        frame = self.build(workers=2, hash_check=True)
        self.assertEqual(list(frame.parse_status), ["ok", "ok"])
        self.assertEqual(list(frame.message_id), ["<first@example.test>", "<second@example.test>"])
        self.assertEqual(frame.iloc[0].attachment_names, "beleg.txt")
        self.assertEqual(frame.iloc[0].sent_date_de, "01.09.2026")
        self.assertIn("Termin bestaetigt.", frame.iloc[1].body_text_clean)
        progress = []
        cached = self.build(hash_check=True, progress_callback=lambda *event: progress.append(event))
        pd.testing.assert_frame_equal(frame, cached)
        self.assertEqual([event[3] for event in progress], ["cache", "cache"])

    def test_exports_match_pre_refactor_snapshot(self):
        frame = portable_frame(self.build(workers=1, hash_check=True))
        expected = json.loads((Path(__file__).parent / "fixtures/exports.json").read_text(encoding="utf-8"))
        actual = {}
        for suffix in ("csv", "json", "xml", "md"):
            path = self.root / f"emails.{suffix}"
            write_output(frame, path)
            actual[suffix] = path.read_text(encoding="utf-8")
        workspace = self.root / "workspace"
        write_markdown_dataset(frame, workspace, "compact")
        for path in sorted(workspace.rglob("*")):
            if path.is_file():
                actual[path.relative_to(workspace).as_posix()] = path.read_text(encoding="utf-8")
        self.assertEqual(actual, expected)
        for suffix, reader in (("parquet", pd.read_parquet), ("xlsx", pd.read_excel)):
            path = self.root / f"emails.{suffix}"
            write_output(frame, path)
            restored = reader(path).fillna("")
            self.assertEqual(list(restored.columns), list(frame.columns))
            self.assertEqual(restored.astype(str).to_dict("records"), frame.astype(str).to_dict("records"))

    def test_changed_source_is_parsed_again(self):
        first = self.build(hash_check=True)
        path = self.source / "first.eml"
        path.write_bytes(path.read_bytes().replace(b"Freigabe erfolgt.", b"Freigabe offen!!"))
        progress = []
        second = self.build(hash_check=True, progress_callback=lambda *event: progress.append(event))
        self.assertNotEqual(first.iloc[0].file_sha256, second.iloc[0].file_sha256)
        self.assertIn("Freigabe offen!!", second.iloc[0].body_text_clean)
        self.assertEqual(sorted(event[3] for event in progress), ["cache", "parsed"])


if __name__ == "__main__":
    unittest.main()
