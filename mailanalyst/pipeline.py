"""Assemble deterministic message results and per-source verification records."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

import pandas as pd

from mailanalyst.cancellation import check_cancel
from mailanalyst.cache import load_cache, save_cache
from mailanalyst.config import LOGGER
from mailanalyst.discovery import discover_mail_files
from mailanalyst.source_processing import process_source


def build_dataframe(
    input_path: Path,
    cache_path: Path,
    refresh: bool = False,
    hash_check: bool = False,
    workers: int = 1,
    timezone_name: str = "Europe/Berlin",
    pst_backend: str = "auto",
    paths_override: list[Path] | None = None,
    progress_callback: Callable[[int, int, Path, str], None] | None = None,
    cancel=None,
) -> pd.DataFrame:
    check_cancel(cancel)
    paths = paths_override if paths_override is not None else discover_mail_files(input_path)
    if any(path.suffix.lower() == ".pst" for path in paths):
        workers = 1
    cached = load_cache(cache_path, refresh)
    results = [None] * len(paths)
    completed = 0

    def accept(index, result):
        nonlocal completed
        check_cancel(cancel)
        results[index] = result
        completed += 1
        audit = result[2]
        LOGGER.info("[%s/%s] %s %s", completed, len(paths), audit["mode"], paths[index])
        if progress_callback:
            progress_callback(completed, len(paths), paths[index], audit["mode"])

    if workers <= 1:
        for index, path in enumerate(paths):
            accept(index, process_source(path, cached, hash_check, timezone_name, pst_backend, cancel))
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_source, path, cached, hash_check, timezone_name, pst_backend, cancel): index
                       for index, path in enumerate(paths)}
            for future in as_completed(futures):
                accept(futures[future], future.result())
    entries = {audit["source_file_path"]: entry for rows, entry, audit in results if not audit["errors"]}
    check_cancel(cancel)
    save_cache(cache_path, entries)
    check_cancel(cancel)
    frame = pd.DataFrame(row for rows, _, _ in results for row in rows)
    frame.attrs["sources"] = [audit for _, _, audit in results]
    return frame
