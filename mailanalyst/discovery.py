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


def discover_all_files(input_path: Path, excluded=()) -> list[Path]:
    """Inventory all files, pruning explicitly excluded output trees."""
    import os
    exclusions = tuple(path.resolve() for path in excluded)

    def allowed(path):
        resolved = path.resolve()
        return not any(resolved == root or resolved.is_relative_to(root) for root in exclusions)

    if input_path.is_file():
        return [input_path] if allowed(input_path) else []
    if not input_path.is_dir():
        raise FileNotFoundError(f"Eingabeordner nicht erreichbar: {input_path}")
    paths = []

    def fail(error):
        raise error

    for directory, folders, files in os.walk(input_path, onerror=fail, followlinks=False):
        base = Path(directory)
        folders[:] = [name for name in folders if allowed(base / name)]
        paths.extend(base / name for name in files if allowed(base / name))
    return sorted(paths)
