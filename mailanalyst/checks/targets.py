"""Checks for selected formats and actual working/output locations."""

import shutil
import tempfile
from pathlib import Path

from mailanalyst.checks.system import SystemCheckResult, _module_available, _classic_outlook_registered


def check_components(paths, formats, backend="auto"):
    required = {"pandas", "bs4"}
    if any(path.suffix.lower() == ".msg" for path in paths):
        required.add("extract_msg")
    if ".parquet" in formats:
        required.add("pyarrow")
    if ".xlsx" in formats:
        required.add("openpyxl")
    results = [SystemCheckResult("Auftrag", module, "ok" if _module_available(module) else "error",
                                 "Fuer die Auswahl erforderlich") for module in sorted(required)]
    if any(path.suffix.lower() == ".pst" for path in paths):
        libpff = _module_available("pypff")
        outlook = _module_available("win32com.client") and _classic_outlook_registered()
        available = libpff if backend == "libpff" else outlook if backend == "outlook" else libpff or outlook
        results.append(SystemCheckResult("Auftrag", f"PST: {backend}", "ok" if available else "error",
                                         "Komponentencheck; kein Nachweis einer erreichbaren Outlook-Sitzung"))
    return results


def check_locations(directories, source_bytes=0):
    results = []
    for directory in sorted({Path(path).resolve() for path in directories}):
        try:
            directory.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=directory, prefix=".mailanalyst-check-", delete=True) as stream:
                stream.write(b"write-check")
                stream.flush()
            free = shutil.disk_usage(directory).free
            estimate = max(16 * 1024 ** 2, source_bytes * 6)
            status = "error" if free < 16 * 1024 ** 2 else "warning" if free < estimate else "ok"
            detail = (f"{free} Bytes frei; grobe Reserve {estimate} Bytes (6x Quellgroesse, mindestens 16 MiB). "
                      "Keine Platzgarantie fuer entpackte Archive oder alle Exportprofile.")
            results.append(SystemCheckResult("Ziel", str(directory), status, detail))
        except OSError as exc:
            results.append(SystemCheckResult("Ziel", str(directory), "error", str(exc)))
    return results


def require_usable(results):
    errors = [f"{row.name}: {row.detail}" for row in results if row.status == "error"]
    if errors:
        raise ValueError("Auftrag nicht ausfuehrbar: " + "; ".join(errors))


def profile_formats(profile):
    return {"Analysepaket": {".parquet", ".json", ".md"}, "Parquet": {".parquet"},
            "CSV": {".csv"}, "JSON": {".json"}, "Markdown": {".md"},
            "Markdown-Monatsordner": {".md"}}[profile]


def validate_source_target(source, target, paths=(), cache=None):
    source, target = source.resolve(), target.resolve()
    if source == target or (source.is_dir() and source.is_relative_to(target)):
        raise ValueError("Quelle und Ziel brauchen getrennte Bereiche; Ziel darf die Quelle nicht enthalten")
    if cache is not None and cache.resolve() in {path.resolve() for path in paths}:
        raise ValueError("Cache darf keine Quelldatei ersetzen")
