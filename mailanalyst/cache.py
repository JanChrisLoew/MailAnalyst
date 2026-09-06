"""Versioned SQLite cache containing JSON data, never executable pickle."""

from contextlib import closing
import json
import os
import sqlite3
import tempfile
from pathlib import Path

from mailanalyst.config import CACHE_SCHEMA_VERSION, LOGGER

STORAGE_VERSION = 1
PARSER_VERSION = 1


def sqlite_path(path: Path) -> Path:
    return path.with_suffix(".sqlite3") if path.suffix.lower() in {".pkl", ".pickle"} else path


def load_cache(path: Path, refresh: bool) -> dict:
    path = sqlite_path(path).resolve()
    if refresh or not path.exists():
        return {}
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as connection:
            if connection.execute("PRAGMA quick_check").fetchone() != ("ok",):
                raise ValueError("SQLite integrity check failed")
            if connection.execute("PRAGMA user_version").fetchone()[0] != STORAGE_VERSION:
                raise ValueError("Unsupported cache version")
            result = {}
            for key, payload in connection.execute("SELECT source, payload FROM sources"):
                entry = json.loads(payload)
                if not isinstance(entry, dict) or set(entry) != {"criteria", "rows"}:
                    raise ValueError("Invalid cache entry")
                expected, rows = entry["criteria"], entry["rows"]
                if not isinstance(expected, dict) or not isinstance(rows, list):
                    raise ValueError("Invalid cache types")
                if set(expected) != {"schema", "parser", "timezone", "backend", "size", "mtime", "sha256"}:
                    raise ValueError("Invalid cache criteria")
                if not isinstance(expected["sha256"], str) or len(expected["sha256"]) != 64:
                    raise ValueError("Invalid source hash")
                if any(type(expected[key]) is not int for key in ("schema", "parser", "size", "mtime")):
                    raise ValueError("Invalid numeric criteria")
                if any(not isinstance(expected[key], str) for key in ("timezone", "backend")):
                    raise ValueError("Invalid parser settings")
                if any(character not in "0123456789abcdef" for character in expected["sha256"]):
                    raise ValueError("Invalid hash encoding")
                for row in rows:
                    if not isinstance(row, dict) or row.get("source_file_path") != key:
                        raise ValueError("Invalid cached source")
                    if row.get("parse_status") != "ok" or not isinstance(row.get("source_path"), str):
                        raise ValueError("Invalid cached row")
                    for field, criterion in (("file_size", "size"), ("modified_at_ns", "mtime"),
                                             ("file_sha256", "sha256"), ("cache_schema_version", "schema")):
                        if row.get(field) != expected[criterion]:
                            raise ValueError("Cache row disagrees with source criteria")
                    if not {"subject", "body_text", "parse_error"}.issubset(row):
                        raise ValueError("Missing message fields")
                    if any(value is not None and type(value) not in (str, int, float, bool) for value in row.values()):
                        raise ValueError("Non-scalar cached value")
                result[key] = entry
            return result
    except (sqlite3.Error, ValueError, TypeError, OSError) as exc:
        LOGGER.warning("Cache wird neu aufgebaut: %s", exc)
        return {}


def criteria(signature, timezone_name: str, backend: str) -> dict:
    return {"schema": CACHE_SCHEMA_VERSION, "parser": PARSER_VERSION, "timezone": timezone_name,
            "backend": backend, "size": signature.file_size, "mtime": signature.modified_at_ns,
            "sha256": signature.file_sha256}


def matches(entry: dict, expected: dict, hash_check: bool) -> bool:
    return all(entry["criteria"].get(key) == value for key, value in expected.items()
               if key != "sha256" or hash_check)


def save_cache(path: Path, entries: dict) -> None:
    path = sqlite_path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="cache-", suffix=".sqlite3", dir=path.parent)
    os.close(fd)
    try:
        with closing(sqlite3.connect(temporary)) as connection:
            connection.execute(f"PRAGMA user_version={STORAGE_VERSION}")
            connection.execute("CREATE TABLE sources (source TEXT PRIMARY KEY, payload TEXT NOT NULL)")
            connection.executemany("INSERT INTO sources VALUES (?, ?)",
                                   [(key, json.dumps(value, ensure_ascii=False, allow_nan=False))
                                    for key, value in entries.items()])
            connection.commit()
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
