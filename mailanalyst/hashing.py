from __future__ import annotations
from pathlib import Path
from datetime import datetime
import hashlib
from datetime import timezone
from mailanalyst.cancellation import check_cancel
from mailanalyst.models import FileSignature


def sha256_file(path: Path, chunk_size: int = 1024 * 1024, cancel=None) -> str:
    """Berechnet einen Datei-Hash fuer Nachvollziehbarkeit und optionale Cache-Pruefung."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            check_cancel(cancel)
            digest.update(chunk)
    return digest.hexdigest()


def file_signature(path: Path, include_hash: bool = False, cancel=None) -> FileSignature:
    """Erfasst stabile Dateimerkmale fuer Cache und Nachweisfuehrung."""
    check_cancel(cancel)
    stat = path.stat()
    return FileSignature(
        source_path=str(path.resolve()),
        file_name=path.name,
        file_ext=path.suffix.lower(),
        file_size=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        modified_at_ns=stat.st_mtime_ns,
        file_sha256=sha256_file(path, cancel=cancel) if include_hash else "",
    )
