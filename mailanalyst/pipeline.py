from __future__ import annotations
from typing import Callable
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import pandas as pd
from mailanalyst.models import FileSignature
from mailanalyst.config import LOGGER
from mailanalyst.cache import cached_row_matches
from mailanalyst.discovery import discover_mail_files
from mailanalyst.hashing import file_signature
from mailanalyst.cache import load_cache
from mailanalyst.parsing.dispatch import parse_mail_file


def parse_indexed_mail(index: int, total: int, path: Path, signature: FileSignature, timezone_name: str, pst_backend: str) -> tuple[int, list[dict[str, object]]]:
    """Hilfsfunktion fuer paralleles Parsen mit stabiler Ergebnisreihenfolge."""
    LOGGER.info("[%s/%s] Parse %s", index + 1, total, path)
    return index, parse_mail_file(path, signature, timezone_name, pst_backend)


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
) -> pd.DataFrame:
    """Baut den vollstaendigen Master-DataFrame aus Cache und neu geparsten Mails."""
    paths = paths_override if paths_override is not None else discover_mail_files(input_path)
    if any(path.suffix.lower() == ".pst" for path in paths):
        workers = 1  # Outlook-COM und PST-Stores werden bewusst seriell verarbeitet.
    cached = load_cache(cache_path, refresh)
    cached_by_path: dict[str, list[dict[str, object]]] = {}
    if not cached.empty and "source_path" in cached.columns:
        for _, row in cached.iterrows():
            key = str(row.get("source_file_path") or row.get("source_path"))
            cached_by_path.setdefault(key, []).append(dict(row))

    rows: list[list[dict[str, object]] | None] = [None] * len(paths)
    parse_jobs: list[tuple[int, Path, FileSignature]] = []
    for index, path in enumerate(paths):
        signature = file_signature(path, include_hash=hash_check)
        cached_rows = cached_by_path.get(signature.key)
        if cached_rows and cached_row_matches(pd.Series(cached_rows[0]), signature, hash_check, pst_backend):
            rows[index] = cached_rows
            if progress_callback:
                progress_callback(index + 1, len(paths), path, "cache")
            continue

        parse_jobs.append((index, path, signature))

    if workers <= 1 or len(parse_jobs) <= 1:
        for index, path, signature in parse_jobs:
            _, row = parse_indexed_mail(index, len(paths), path, signature, timezone_name, pst_backend)
            rows[index] = row
            if progress_callback:
                progress_callback(index + 1, len(paths), path, "parsed")
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(parse_indexed_mail, index, len(paths), path, signature, timezone_name, pst_backend)
                for index, path, signature in parse_jobs
            ]
            for future in as_completed(futures):
                index, row = future.result()
                rows[index] = row
                if progress_callback:
                    completed = sum(item is not None for item in rows)
                    progress_callback(completed, len(paths), paths[index], "parsed")

    dataframe = pd.DataFrame(row for source_rows in rows if source_rows is not None for row in source_rows)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_pickle(cache_path)
    return dataframe
