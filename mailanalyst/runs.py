"""Run manifests and publication of validated export packages."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from mailanalyst.config import CACHE_SCHEMA_VERSION, LOGGER
from mailanalyst.cache import PARSER_VERSION, STORAGE_VERSION
from mailanalyst.hashing import sha256_file


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class Run:
    def __init__(self, target: Path, options: dict):
        self.root = target.resolve() / "runs" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex)
        self.pending = self.root / ".pending"
        self.pending.mkdir(parents=True)
        self.data = {"manifest_version": 1, "run_id": self.root.name, "status": "running",
                     "started_at": utc_now(), "finished_at": None, "options": options,
                     "versions": {"cache": STORAGE_VERSION, "schema": CACHE_SCHEMA_VERSION, "parser": PARSER_VERSION},
                     "sources": [], "outputs": [], "error": None}
        self.write_manifest()

    def write_manifest(self):
        path = self.root / "manifest.json"
        temporary = self.root / ".manifest.tmp"
        temporary.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, path)

    def record_frame(self, frame):
        self.data["sources"] = frame.attrs.get("sources", [])
        self.data["messages"] = len(frame)
        self.data["parser_errors"] = sum(source["errors"] for source in self.data["sources"])
        self.data["cache_hits"] = sum(source["mode"] == "cache" for source in self.data["sources"])
        if "parse_status" in frame:
            for _, row in frame[frame["parse_status"] == "error"].iterrows():
                LOGGER.error("Parse-Fehler: %s | %s", row.get("source_path", ""), row.get("parse_error", ""))
        self.write_manifest()

    def publish(self):
        outputs = [{"path": "exports/" + path.relative_to(self.pending).as_posix(),
                    "size": path.stat().st_size, "sha256": sha256_file(path)}
                   for path in sorted(self.pending.rglob("*")) if path.is_file()]
        self.pending.rename(self.root / "exports")
        self.data["outputs"] = outputs

    def finish(self):
        self.data["status"] = "completed_with_errors" if self.data["parser_errors"] else "completed"
        self.data["finished_at"] = utc_now()
        self.data["elapsed_seconds"] = (datetime.fromisoformat(self.data["finished_at"]) -
                                        datetime.fromisoformat(self.data["started_at"])).total_seconds()
        LOGGER.info("Fertig: %s Nachrichten, %s Parserfehler, %s Cachetreffer. Ausgabe: %s",
                    self.data["messages"], self.data["parser_errors"], self.data["cache_hits"], self.root)
        self.write_manifest()

    def fail(self, error, status="failed"):
        self.data.update(status=status, finished_at=utc_now(), error=str(error))
        self.write_manifest()
        if status == "cancelled":
            LOGGER.info("Lauf abgebrochen: %s", self.root)
        else:
            LOGGER.error("Lauf fehlgeschlagen: %s | %s", self.root, error)
