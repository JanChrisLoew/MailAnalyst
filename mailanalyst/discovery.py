from __future__ import annotations
from pathlib import Path
from mailanalyst.config import SUPPORTED_EXTENSIONS


def discover_mail_files(input_path: Path) -> list[Path]:
    """Findet unterstuetzte Maildateien rekursiv oder akzeptiert eine einzelne Datei."""
    if input_path.is_file():
        return [input_path] if input_path.suffix.lower() in SUPPORTED_EXTENSIONS else []
    return sorted(
        path
        for path in input_path.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )
