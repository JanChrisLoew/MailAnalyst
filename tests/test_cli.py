"""Verify both supported command-line entry points in separate processes."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.samples import create_sources

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_script_and_package_entrypoints_export_the_same_data(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = create_sources(root)
            outputs = []
            for index, entry in enumerate(([str(ROOT / "mail_analyst.py")], ["-m", "mailanalyst"])):
                target = root / str(index)
                result = subprocess.run(
                    [sys.executable, *entry, "--input", str(source), "--output", str(target / "emails.json"),
                     "--list-output", str(target / "list.csv"), "--markdown-dir", str(target / "workspace"),
                     "--cache", str(target / "cache.pkl"), "--hash-check", "--workers", "2"],
                    cwd=ROOT, capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                outputs.append(json.loads((target / "emails.json").read_text(encoding="utf-8")))
                self.assertTrue((target / "list.csv").exists())
                self.assertTrue((target / "workspace/index.jsonl").exists())
                self.assertIn("Fertig:", (target / "parse_log.txt").read_text(encoding="utf-8"))
            self.assertEqual(outputs[0], outputs[1])
