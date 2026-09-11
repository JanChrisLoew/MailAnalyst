"""Disk-backed messages, deterministic order and bounded export batches."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from mailanalyst.cancellation import check_cancel
from mailanalyst.message_schema import assess_message

BATCH_SIZE = 500
BATCH_BYTES = 8 * 1024 * 1024
STORE_VERSION = 2


class RecordStore:
    def __init__(self, path: Path, cancel=None):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA cache_size=-8192")
        self.db.execute("PRAGMA temp_store=FILE")
        self.db.execute(f"PRAGMA user_version={STORE_VERSION}")
        self.db.executescript("""
            CREATE TABLE sources (source TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE messages (seq INTEGER PRIMARY KEY, source TEXT, payload TEXT,
                                   sent TEXT, chunk TEXT, subject TEXT);
            CREATE TABLE quality_warnings (seq INTEGER, source_path TEXT, payload TEXT);
            CREATE INDEX source_rows ON messages(source, seq);
        """)
        self.columns = {}
        self.count = 0
        self.source_count = 0
        self.errors = 0
        self.warning_count = 0
        self.warning_messages = 0
        self.cancel = cancel
        self.batch_size = BATCH_SIZE
        self.max_batch_rows = 0
        self.max_batch_bytes = 0
        self.on_flush = None

    def __len__(self):
        return self.count

    def append(self, source, rows):
        buffer, warning_buffer, size = [], [], 0
        for row in rows:
            check_cancel(self.cancel)
            warnings = assess_message(row)
            payload = json.dumps(row, ensure_ascii=False, allow_nan=False)
            for key, value in row.items():
                self.columns.setdefault(key, set())
                if value is not None:
                    self.columns[key].add(type(value).__name__)
            try:
                sent = datetime.fromisoformat(row.get("sent_at_utc", ""))
                sent = sent.replace(tzinfo=timezone.utc) if sent.tzinfo is None else sent.astimezone(timezone.utc)
                date, chunk = sent.isoformat(), sent.strftime("%Y-%m")
            except (ValueError, TypeError):
                date, chunk = None, "unbekannt"
            buffer.append((source, payload, date, chunk, str(row.get("subject", "") or "")))
            seq = self.count + 1
            warning_buffer.extend((seq, row["source_path"], json.dumps(item, ensure_ascii=False))
                                  for item in warnings)
            size += len(payload.encode("utf-8"))
            self.count += 1
            self.errors += row.get("parse_status") == "error"
            self.warning_count += len(warnings)
            self.warning_messages += bool(warnings)
            if len(buffer) >= self.batch_size or size >= BATCH_BYTES:
                self._flush(buffer, warning_buffer, size)
                buffer, warning_buffer, size = [], [], 0
        self._flush(buffer, warning_buffer, size)

    def _flush(self, buffer, warnings, size):
        self.max_batch_rows = max(self.max_batch_rows, len(buffer))
        self.max_batch_bytes = max(self.max_batch_bytes, size)
        self.db.executemany("INSERT INTO messages(source,payload,sent,chunk,subject) VALUES (?,?,?,?,?)", buffer)
        self.db.executemany("INSERT INTO quality_warnings VALUES (?,?,?)", warnings)
        if buffer and self.on_flush:
            self.on_flush()

    def add_source(self, source, criteria, audit):
        self.db.execute("INSERT INTO sources VALUES (?,?)", (source, json.dumps({"criteria": criteria, "audit": audit})))
        self.source_count += 1
        if self.source_count % self.batch_size == 0:
            self.db.commit()

    def records(self, chunk=None):
        check_cancel(self.cancel)
        sql, params = "SELECT payload FROM messages ORDER BY seq", ()
        if chunk is not None:
            sql, params = "SELECT payload FROM messages WHERE chunk=? ORDER BY sent IS NULL,sent,subject,seq", (chunk,)
        cursor = self.db.execute(sql, params)
        try:
            for (payload,) in cursor:
                check_cancel(self.cancel)
                row = json.loads(payload)
                yield {key: row.get(key) for key in self.columns}
        finally:
            cursor.close()

    def batches(self):
        batch, size = [], 0
        for row in self.records():
            batch.append(row)
            size += sum(len(value.encode("utf-8")) for value in row.values() if isinstance(value, str))
            if len(batch) >= self.batch_size or size >= BATCH_BYTES:
                yield batch
                batch, size = [], 0
        if batch:
            yield batch

    def chunks(self):
        self.db.execute("CREATE INDEX IF NOT EXISTS month_order ON messages(chunk,sent,subject,seq)")
        yield from self.db.execute("SELECT chunk,COUNT(*) FROM messages GROUP BY chunk ORDER BY chunk")

    def audits(self):
        for (payload,) in self.db.execute("SELECT payload FROM sources ORDER BY rowid"):
            yield json.loads(payload)["audit"]

    def quality_warnings(self):
        for seq, source_path, payload in self.db.execute(
                "SELECT seq,source_path,payload FROM quality_warnings ORDER BY seq,rowid"):
            yield {"message_number": seq, "source_path": source_path, **json.loads(payload)}

    def preview(self, limit=500):
        rows, size = [], 0
        for (payload,) in self.db.execute("SELECT payload FROM messages ORDER BY seq LIMIT ?", (limit,)):
            check_cancel(self.cancel)
            rows.append(json.loads(payload))
            size += len(payload.encode("utf-8"))
            if size >= BATCH_BYTES:
                break
        frame = pd.DataFrame(rows, columns=list(self.columns))
        frame.attrs.update(total_messages=self.count, total_errors=self.errors, preview_limit=limit)
        return frame

    def close(self):
        self.db.close()
