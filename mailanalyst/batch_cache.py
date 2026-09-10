"""Read individual sources and publish a bounded-memory SQLite cache."""

import json
import math
import os
import sqlite3
import tempfile
from contextlib import closing

from mailanalyst.cache import sqlite_path
from mailanalyst.cancellation import check_cancel
from mailanalyst.config import LOGGER
from mailanalyst.record_store import STORE_VERSION


class BatchCache:
    def __init__(self, path, refresh=False, cancel=None):
        self.cancel = cancel
        self.db = None
        path = sqlite_path(path).resolve()
        if refresh or not path.exists():
            return
        try:
            self.db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
            self.db.execute("PRAGMA cache_size=-4096")
            if self.db.execute("PRAGMA user_version").fetchone()[0] != STORE_VERSION:
                raise ValueError("Cacheformat wird auf Einzelzeilen umgestellt")
            if self.db.execute("PRAGMA quick_check").fetchone() != ("ok",):
                raise ValueError("Beschaedigter Cache")
            self.db.execute("SELECT source,payload FROM sources LIMIT 0")
            self.db.execute("SELECT source,seq,payload FROM messages LIMIT 0")
        except (sqlite3.Error, ValueError) as exc:
            LOGGER.warning("Cache wird neu aufgebaut: %s", exc)
            self.close()

    def lookup(self, source):
        if self.db is None:
            return None
        try:
            found = self.db.execute("SELECT payload FROM sources WHERE source=?", (source,)).fetchone()
            if found is None:
                return None
            item = json.loads(found[0])
            expected, audit = item["criteria"], item["audit"]
            if audit["errors"] or audit["source_file_path"] != source:
                return None
            if set(expected) != {"schema", "parser", "timezone", "backend", "size", "mtime", "sha256"}:
                raise ValueError("Invalid cache criteria")
            if not isinstance(expected["sha256"], str) or len(expected["sha256"]) != 64:
                raise ValueError("Invalid source hash")
            count = self.db.execute("SELECT COUNT(*) FROM messages WHERE source=?", (source,)).fetchone()[0]
            if count != audit["messages"]:
                raise ValueError("Incomplete cache source")
            # Validate a source before copying any rows to the run store.
            for row in self.rows(source):
                if row.get("source_file_path") != source or row.get("parse_status") != "ok":
                    raise ValueError("Invalid cache row")
                for field, key in (("file_size", "size"), ("modified_at_ns", "mtime"),
                                   ("file_sha256", "sha256"), ("cache_schema_version", "schema")):
                    if row.get(field) != expected[key]:
                        raise ValueError("Cache criteria mismatch")
            return item
        except (sqlite3.Error, ValueError, KeyError, TypeError) as exc:
            LOGGER.warning("Cachequelle wird neu gelesen: %s", exc)
            return None

    def rows(self, source):
        for (payload,) in self.db.execute("SELECT payload FROM messages WHERE source=? ORDER BY seq", (source,)):
            check_cancel(self.cancel)
            row = json.loads(payload)
            if not isinstance(row, dict) or any(value is not None and type(value) not in (str, int, float, bool) for value in row.values()):
                raise ValueError("Invalid message data")
            if any(type(value) is float and not math.isfinite(value) for value in row.values()):
                raise ValueError("Non-finite message value")
            yield row

    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None


def publish_cache(store, path):
    path = sqlite_path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="cache-", suffix=".sqlite3", dir=path.parent)
    os.close(fd)
    try:
        store.db.commit()
        with closing(sqlite3.connect(temporary)) as target:
            store.db.backup(target, pages=256, progress=lambda *_: check_cancel(store.cancel))
        check_cancel(store.cancel)
        os.replace(temporary, path)
    finally:
        from pathlib import Path
        Path(temporary).unlink(missing_ok=True)
