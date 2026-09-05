from __future__ import annotations
from pathlib import Path
import pandas as pd
from mailanalyst.config import CACHE_SCHEMA_VERSION
from mailanalyst.models import FileSignature


def load_cache(cache_path: Path, refresh: bool) -> pd.DataFrame:
    """Laedt den DataFrame-Cache, sofern kein kompletter Neuaufbau angefordert ist."""
    if refresh or not cache_path.exists():
        return pd.DataFrame()
    return pd.read_pickle(cache_path)


def cached_row_matches(cached_row: pd.Series, signature: FileSignature, hash_check: bool, pst_backend: str) -> bool:
    """Prueft, ob eine Cache-Zeile fuer die aktuelle Datei wiederverwendet werden darf."""
    if cached_row.get("cache_schema_version") != CACHE_SCHEMA_VERSION:
        return False
    if cached_row.get("file_size") != signature.file_size:
        return False
    if cached_row.get("modified_at_ns") != signature.modified_at_ns:
        return False
    if hash_check and cached_row.get("file_sha256") != signature.file_sha256:
        return False
    if signature.file_ext == ".pst" and pst_backend != "auto" and cached_row.get("pst_backend") != pst_backend:
        return False
    return True
