"""Stream an archive into the run store and verify it before acceptance."""

from contextlib import closing
from datetime import datetime, timezone

from mailanalyst.cache import criteria, matches
from mailanalyst.hashing import file_signature
from mailanalyst.parsing.dispatch import iter_mail_file, resolve_pst_backend
from mailanalyst.source_guard import require_preflight


def append_archive(store, cache, path, hash_check, timezone_name, pst_backend, preflight=None):
    cancel = store.cancel
    hash_check = hash_check or preflight is not None
    backend = resolve_pst_backend(pst_backend)
    before = file_signature(path, include_hash=hash_check, cancel=cancel)
    require_preflight(before, preflight)
    expected = criteria(before, timezone_name, backend)
    entry = cache.lookup(before.key)
    hit = entry is not None and matches(entry, expected, hash_check)
    if not hit:
        before = file_signature(path, include_hash=True, cancel=cancel)
        require_preflight(before, preflight)
        expected = criteria(before, timezone_name, backend)
    iterator = cache.rows(before.key) if hit else iter_mail_file(path, before, timezone_name, backend)
    count, errors = len(store), store.errors
    with closing(iterator):
        store.append(before.key, iterator)
    after = file_signature(path, include_hash=hash_check or not hit, cancel=cancel)
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
             "messages": len(store) - count, "errors": store.errors - errors}
    store.add_source(before.key, expected, audit)
    return audit
