"""Compact, published result index with bounded read-only pages."""

from contextlib import closing
import json
import sqlite3

from mailanalyst.cancellation import check_cancel

FIELDS = ("sent_datetime_de", "from_email", "subject", "file_ext", "parse_status", "parse_error", "source_path")
PAGE_SIZE = 500


def write_review(store, path):
    with closing(sqlite3.connect(path)) as db:
        db.execute("CREATE TABLE review (seq INTEGER PRIMARY KEY, status TEXT, payload TEXT)")
        batch = []
        for row in store.records():
            check_cancel(store.cancel)
            # No message bodies; complete error and source references remain available.
            values = {key: str(row.get(key) or "") for key in FIELDS}
            batch.append((values["parse_status"], json.dumps(values, ensure_ascii=False)))
            if len(batch) == PAGE_SIZE:
                db.executemany("INSERT INTO review(status,payload) VALUES (?,?)", batch)
                batch.clear()
        db.executemany("INSERT INTO review(status,payload) VALUES (?,?)", batch)
        db.execute("CREATE INDEX review_status ON review(status,seq)")
        db.commit()
        if db.execute("SELECT COUNT(*) FROM review").fetchone()[0] != len(store):
            raise ValueError("Ergebnisindex unvollstaendig")


def read_review(path, offset=0, status="", limit=PAGE_SIZE):
    if offset < 0 or not 1 <= limit <= PAGE_SIZE:
        raise ValueError("Invalid result page")
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        where, params = (" WHERE status=?", (status,)) if status else ("", ())
        total = db.execute("SELECT COUNT(*) FROM review" + where, params).fetchone()[0]
        rows = db.execute("SELECT seq,payload FROM review" + where + " ORDER BY seq LIMIT ? OFFSET ?",
                          (*params, limit, offset))
        return [(seq, json.loads(payload)) for seq, payload in rows], total
