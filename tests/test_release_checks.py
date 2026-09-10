"""Version propagation and actionable component/target failures."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from mailanalyst.checks.targets import check_components, check_locations, require_usable
from mailanalyst.runs import Run
from mailanalyst.version import APP_VERSION, build_info


class ReleaseChecksTests(unittest.TestCase):
    def test_cli_version_and_manifest_agree(self):
        result = subprocess.run([sys.executable, "-m", "mailanalyst", "--version"],
                                capture_output=True, text=True, check=True)
        self.assertIn(APP_VERSION, result.stdout)
        with tempfile.TemporaryDirectory() as temp:
            run = Run(Path(temp), {})
            saved = json.loads((run.root / "manifest.json").read_text())
            self.assertEqual(saved["application"]["app_version"], APP_VERSION)

    def test_packaged_build_metadata_is_read_without_git(self):
        with tempfile.TemporaryDirectory() as temp:
            expected = {"app_version": APP_VERSION, "source_revision": "synthetic", "source_dirty": True}
            (Path(temp) / "build_info.json").write_text(json.dumps(expected))
            with patch.object(sys, "frozen", True, create=True), patch.object(sys, "_MEIPASS", temp, create=True):
                self.assertEqual(build_info(), expected)

    def test_missing_optional_backend_does_not_block_eml_json(self):
        available = lambda module: module in {"pandas", "bs4"}
        with patch("mailanalyst.checks.targets._module_available", side_effect=available):
            require_usable(check_components([Path("mail.eml")], {".json"}))
            with self.assertRaisesRegex(ValueError, "pyarrow"):
                require_usable(check_components([Path("mail.eml")], {".parquet"}))
            with self.assertRaisesRegex(ValueError, "extract_msg"):
                require_usable(check_components([Path("mail.msg")], {".json"}))
            with self.assertRaisesRegex(ValueError, "PST"):
                require_usable(check_components([Path("mail.pst")], {".json"}, "libpff"))

    def test_actual_target_write_probe_and_disk_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "new"
            require_usable(check_locations([target]))
            self.assertEqual(list(target.iterdir()), [])
            with patch("mailanalyst.checks.targets.shutil.disk_usage", return_value=SimpleNamespace(free=0)):
                with self.assertRaisesRegex(ValueError, "Bytes frei"):
                    require_usable(check_locations([target]))
            with patch("mailanalyst.checks.targets.tempfile.NamedTemporaryFile", side_effect=PermissionError("locked")):
                with self.assertRaisesRegex(ValueError, "locked"):
                    require_usable(check_locations([target]))
