"""Bounded EML/MSG concurrency and streaming PST processing for CLI/GUI."""

from concurrent.futures import ThreadPoolExecutor

from mailanalyst.batch_cache import BatchCache, publish_cache
from mailanalyst.batch_sources import append_archive
from mailanalyst.cancellation import check_cancel
from mailanalyst.config import LOGGER
from mailanalyst.discovery import discover_mail_files
from mailanalyst.record_store import RecordStore, BATCH_SIZE
from mailanalyst.source_processing import process_source


def build_store(input_path, cache_path, store_path, refresh=False, hash_check=False, workers=1,
                timezone_name="Europe/Berlin", pst_backend="auto", paths_override=None,
                progress_callback=None, cancel=None, batch_size=BATCH_SIZE, phase_progress=None, preflight=None):
    if not 1 <= batch_size <= 5000:
        raise ValueError("batch_size muss zwischen 1 und 5000 liegen")
    if workers < 1 or workers > 32:
        raise ValueError("workers muss zwischen 1 und 32 liegen")
    check_cancel(cancel)
    if phase_progress:
        phase_progress("Quellen prüfen", "Quellen und Cache vorbereiten")
    paths = list(paths_override) if paths_override is not None else discover_mail_files(input_path)
    if preflight is not None and any(str(path.resolve()) not in preflight for path in paths):
        raise ValueError("Auswahl nicht vollstaendig vorgeprueft")
    cache = BatchCache(cache_path, refresh, cancel)
    store = RecordStore(store_path, cancel)
    store.batch_size = batch_size
    completed = 0

    def notify(path, audit):
        nonlocal completed
        completed += 1
        if phase_progress:
            phase_progress("Nachrichten lesen", str(path.name), len(store))
        LOGGER.info("[%s/%s] %s %s", completed, len(paths), audit["mode"], path)
        if progress_callback and (len(paths) <= 1000 or completed % 50 == 0 or completed == len(paths)):
            progress_callback(completed, len(paths), path, audit["mode"])

    try:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            index = 0
            while index < len(paths):
                check_cancel(cancel)
                if paths[index].suffix.lower() == ".pst":
                    path = paths[index]
                    if phase_progress:
                        phase_progress("Nachrichten lesen", path.name, len(store))
                    if progress_callback or phase_progress:
                        def archive_progress():
                            if progress_callback:
                                progress_callback(completed, len(paths), path, f"{len(store)} Nachrichten gelesen")
                            if phase_progress:
                                phase_progress("Nachrichten lesen", path.name, len(store))
                        store.on_flush = archive_progress
                    expected = preflight[str(path.resolve())] if preflight is not None else None
                    audit = append_archive(store, cache, path, hash_check, timezone_name, pst_backend, expected)
                    store.on_flush = None
                    notify(path, audit)
                    index += 1
                    continue
                pending = []
                while index < len(paths) and len(pending) < min(batch_size, workers * 2):
                    path = paths[index]
                    if path.suffix.lower() == ".pst":
                        break
                    if phase_progress:
                        phase_progress("Nachrichten lesen", path.name, len(store))
                    key = str(path.resolve())
                    item = cache.lookup(key)
                    cached = {}
                    if item is not None and item["audit"]["messages"] <= 1:
                        cached[key] = {"criteria": item["criteria"], "rows": list(cache.rows(key))}
                    expected = preflight[key] if preflight is not None else None
                    job = executor.submit(process_source, path, cached, hash_check, timezone_name, pst_backend, cancel, expected)
                    pending.append((path, job))
                    index += 1
                for path, job in pending:
                    rows, entry, audit = job.result()
                    check_cancel(cancel)
                    store.append(audit["source_file_path"], rows)
                    store.add_source(audit["source_file_path"], entry["criteria"], audit)
                    notify(path, audit)
        check_cancel(cancel)
        cache.close()
        if phase_progress:
            phase_progress("Cache speichern", "Geprüfte Nachrichten sichern", len(store))
        publish_cache(store, cache_path)
        check_cancel(cancel)
        return store
    except BaseException:
        store.close()
        raise
    finally:
        cache.close()
