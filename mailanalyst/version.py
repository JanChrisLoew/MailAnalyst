"""Application version, independent from cache and parser revisions."""

import json
from pathlib import Path
import sys

APP_VERSION = "0.5.0-dev.1"


def build_info():
    if getattr(sys, "frozen", False):
        path = Path(sys._MEIPASS) / "build_info.json"
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"app_version": APP_VERSION, "build_status": "unknown"}
    return {"app_version": APP_VERSION, "build_status": "development"}
