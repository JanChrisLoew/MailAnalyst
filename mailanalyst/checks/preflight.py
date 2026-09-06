from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from email import policy
from email.parser import BytesHeaderParser
from pathlib import Path

import pandas as pd

from mailanalyst.exports.tabular import write_csv
from mailanalyst.discovery import discover_mail_files


OLE_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")
PST_SIGNATURE = b"!BDN"


@dataclass
class PreflightResult:
    path: str
    extension: str
    size: int
    modified_at_ns: int
    status: str
    reason: str
    include: bool


def _check_eml(path: Path) -> tuple[str, str]:
    with path.open("rb") as file:
        sample = file.read(512 * 1024)
    if b"\n\n" not in sample and b"\r\n\r\n" not in sample:
        return "error", "Kein gueltiger Header-/Body-Trenner gefunden"
    message = BytesHeaderParser(policy=policy.default).parsebytes(sample)
    useful_headers = ("From", "To", "Date", "Subject", "Message-ID", "Content-Type")
    if not any(message.get(name) for name in useful_headers):
        return "error", "Keine typischen E-Mail-Header gefunden"
    defects = [defect.__class__.__name__ for defect in getattr(message, "defects", [])]
    if defects:
        return "warning", "MIME-Auffaelligkeiten: " + ", ".join(defects)
    return "ok", "EML-Header plausibel"


def check_file(path: Path) -> PreflightResult:
    try:
        before = path.stat()
        if before.st_size == 0:
            return PreflightResult(str(path.resolve()), path.suffix.lower(), 0, before.st_mtime_ns,
                                   "error", "Datei ist leer", False)
        with path.open("rb") as file:
            signature = file.read(8)
        extension = path.suffix.lower()
        if extension == ".eml":
            status, reason = _check_eml(path)
        elif extension == ".msg":
            status, reason = ("ok", "OLE-/MSG-Signatur plausibel") if signature == OLE_SIGNATURE else (
                "error", "Ungueltige MSG-/OLE-Signatur")
        elif extension == ".pst":
            status, reason = ("ok", "PST-Signatur plausibel") if signature[:4] == PST_SIGNATURE else (
                "error", "Ungueltige PST-Signatur")
        else:
            status, reason = "ignored", "Nicht unterstuetztes Format"
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            status, reason = "warning", "Datei wurde waehrend der Pruefung geaendert"
        return PreflightResult(str(path.resolve()), extension, after.st_size, after.st_mtime_ns,
                               status, reason, status in {"ok", "warning"})
    except PermissionError:
        return PreflightResult(str(path.resolve()), path.suffix.lower(), 0, 0,
                               "error", "Datei ist nicht lesbar oder gesperrt", False)
    except Exception as exc:
        return PreflightResult(str(path.resolve()), path.suffix.lower(), 0, 0,
                               "error", str(exc), False)


def run_preflight(input_path: Path, progress=None) -> list[PreflightResult]:
    files = discover_mail_files(input_path)
    results = []
    for index, path in enumerate(files, start=1):
        results.append(check_file(path))
        if progress:
            progress(index, len(files), path)
    return results


def write_preflight_report(results: list[PreflightResult], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = [asdict(result) for result in results]
    write_csv(pd.DataFrame(rows), output_dir / "preflight_report.csv")
    with (output_dir / "preflight_report.json").open("w", encoding="utf-8") as file:
        json.dump(rows, file, ensure_ascii=False, indent=2)
