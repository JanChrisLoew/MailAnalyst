from __future__ import annotations

import csv
import importlib.metadata
import importlib.util
import json
import platform
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from mailanalyst.text.cells import csv_text


@dataclass
class SystemCheckResult:
    category: str
    name: str
    status: str
    detail: str


ProgressCallback = Callable[[int, int, str], None]


def _module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _package_result(category: str, label: str, module_name: str, distribution: str, required: bool) -> SystemCheckResult:
    if not _module_available(module_name):
        status = "error" if required else "warning"
        role = "erforderlich" if required else "optional"
        return SystemCheckResult(category, label, status, f"Paket fehlt ({role})")
    try:
        version = importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        version = "gebuendelt"
    return SystemCheckResult(category, label, "ok", f"Verfuegbar, Version {version}")


def _classic_outlook_registered() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Outlook.Application\CLSID") as key:
            value, _ = winreg.QueryValueEx(key, None)
            return bool(value)
    except OSError:
        return False


def run_system_check(
    progress: ProgressCallback | None = None,
    detected_font_family: str | None = None,
) -> list[SystemCheckResult]:
    results: list[SystemCheckResult] = []
    checks: list[tuple[str, Callable[[], SystemCheckResult]]] = [
        ("Python-Laufzeit", lambda: SystemCheckResult(
            "Laufzeit", "Python-Laufzeit",
            "ok" if sys.version_info >= (3, 10) else "error",
            f"Python {platform.python_version()} · {platform.architecture()[0]} · {'portable EXE' if getattr(sys, 'frozen', False) else 'Entwicklungsumgebung'}",
        )),
        ("Corporate-Schrift", lambda: SystemCheckResult(
            "Darstellung", "Corporate-Schrift Mulish",
            "ok" if detected_font_family == "Mulish" else "warning",
            "Mulish wurde lokal geladen und ist aktiv" if detected_font_family == "Mulish"
            else f"Mulish ist nicht aktiv; verwendet wird {detected_font_family or 'ein System-Fallback'}",
        )),
        ("Pandas", lambda: _package_result("Kernpaket", "Tabellenverarbeitung", "pandas", "pandas", True)),
        ("Beautiful Soup", lambda: _package_result("Kernpaket", "HTML-Aufbereitung", "bs4", "beautifulsoup4", True)),
        ("MSG-Importer", lambda: _package_result("Mail-Importer", "MSG-Dateien", "extract_msg", "extract-msg", False)),
        ("Parquet", lambda: _package_result("Ausgabeformat", "Parquet", "pyarrow", "pyarrow", False)),
        ("Excel", lambda: _package_result("Ausgabeformat", "Excel", "openpyxl", "openpyxl", False)),
        ("Outlook-Schnittstelle", lambda: _package_result("PST-Importer", "Outlook-Schnittstelle", "win32com.client", "pywin32", False)),
        ("libpff", lambda: _package_result("PST-Importer", "PST ohne Outlook (libpff)", "pypff", "libpff-python", False)),
        ("Klassisches Outlook", lambda: SystemCheckResult(
            "PST-Importer", "Klassisches Outlook",
            "ok" if _classic_outlook_registered() else "warning",
            "Lokale COM-Schnittstelle ist registriert" if _classic_outlook_registered() else "Keine klassische Outlook-COM-Installation erkannt",
        )),
        ("PST-Verarbeitungsweg", lambda: SystemCheckResult(
            "PST-Importer", "Mindestens ein PST-Verarbeitungsweg",
            "ok" if (_module_available("pypff") or (_module_available("win32com.client") and _classic_outlook_registered())) else "warning",
            "PST-Verarbeitung ist verfuegbar" if (_module_available("pypff") or (_module_available("win32com.client") and _classic_outlook_registered())) else "PST kann in dieser Umgebung derzeit nicht verarbeitet werden",
        )),
        ("Temporärer Schreibtest", _temporary_write_check),
        ("Freier Speicherplatz", _disk_space_check),
        ("Lokaler Betrieb", lambda: SystemCheckResult(
            "Datenschutz", "Lokaler Betrieb", "ok", "Keine Cloud-API und kein Netzwerkdienst fuer den Workflow erforderlich",
        )),
    ]

    total = len(checks)
    for done, (label, check) in enumerate(checks, start=1):
        if progress:
            progress(done - 1, total, label)
        try:
            results.append(check())
        except Exception as exc:
            results.append(SystemCheckResult("System", label, "error", f"Pruefung fehlgeschlagen: {exc}"))
        if progress:
            progress(done, total, label)
    return results


def _temporary_write_check() -> SystemCheckResult:
    try:
        with tempfile.NamedTemporaryFile(prefix="mailanalyst_", suffix=".tmp", delete=True) as test_file:
            test_file.write(b"MailAnalyst")
            test_file.flush()
        return SystemCheckResult("Dateisystem", "Temporärer Schreibzugriff", "ok", str(Path(tempfile.gettempdir())))
    except Exception as exc:
        return SystemCheckResult("Dateisystem", "Temporärer Schreibzugriff", "error", str(exc))


def _disk_space_check() -> SystemCheckResult:
    free_bytes = shutil.disk_usage(tempfile.gettempdir()).free
    free_gib = free_bytes / (1024 ** 3)
    status = "ok" if free_gib >= 2 else "warning" if free_gib >= 0.25 else "error"
    return SystemCheckResult("Dateisystem", "Freier Speicherplatz", status, f"{free_gib:.1f} GiB auf dem temporaeren Laufwerk frei")


def write_system_check_report(results: list[SystemCheckResult], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "system_check_report.json"
    csv_path = output_dir / "system_check_report.csv"
    with json_path.open("w", encoding="utf-8") as file:
        json.dump([asdict(result) for result in results], file, ensure_ascii=False, indent=2)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=("category", "name", "status", "detail"))
        writer.writeheader()
        writer.writerows({key: csv_text(value) for key, value in asdict(result).items()} for result in results)
    return csv_path, json_path
