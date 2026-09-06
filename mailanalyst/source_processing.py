"""Process a source and record the scope of its integrity verification."""

from datetime import datetime, timezone

from mailanalyst.cancellation import check_cancel
from mailanalyst.cache import criteria, matches
from mailanalyst.hashing import file_signature
from mailanalyst.parsing.dispatch import parse_mail_file, resolve_pst_backend


def process_source(path, cached, hash_check, timezone_name, pst_backend, cancel=None):
    check_cancel(cancel)
    backend = resolve_pst_backend(pst_backend) if path.suffix.lower() == ".pst" else ""
    before = file_signature(path, include_hash=hash_check, cancel=cancel)
    expected = criteria(before, timezone_name, backend)
    entry = cached.get(before.key)
    hit = entry is not None and matches(entry, expected, hash_check)
    if hit:
        rows = entry["rows"]
        after = file_signature(path, include_hash=hash_check, cancel=cancel)
    else:
        before = file_signature(path, include_hash=True, cancel=cancel)
        expected = criteria(before, timezone_name, backend)
        check_cancel(cancel)
        rows = parse_mail_file(path, before, timezone_name, backend or pst_backend)
        after = file_signature(path, include_hash=True, cancel=cancel)
    if before != after:
        raise RuntimeError(f"Quelle waehrend der Verarbeitung geaendert: {path}")
    verified = hash_check or not hit
    digest = before.file_sha256 if verified else entry["criteria"]["sha256"]
    expected["sha256"] = digest
    audit = {"source_file_path": before.key, "file_size": before.file_size,
             "modified_at_ns": before.modified_at_ns, "file_sha256": digest,
             "hash_status": "verified_this_run" if verified else "reused_unverified",
             "hash_verified_at": datetime.now(timezone.utc).isoformat() if verified else None,
             "mode": "cache" if hit else "parsed", "pst_backend": backend,
             "messages": len(rows), "errors": sum(row.get("parse_status") == "error" for row in rows)}
    return rows, {"criteria": expected, "rows": rows}, audit
