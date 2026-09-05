from __future__ import annotations
from pathlib import Path
import argparse
from datetime import datetime
import os
from datetime import timezone
from mailanalyst.config import DEFAULT_CACHE
from mailanalyst.config import LOGGER
from mailanalyst.pipeline import build_dataframe
from mailanalyst.logging_setup import configure_logging
from mailanalyst.logging_setup import default_log_path
from mailanalyst.exports.tabular import list_export_dataframe
from mailanalyst.exports.markdown import write_markdown_dataset
from mailanalyst.exports.dispatch import write_output


def parse_args() -> argparse.Namespace:
    """Definiert die Kommandozeilenoptionen fuer den Batchlauf."""
    parser = argparse.ArgumentParser(description="Outlook-Dateien (.eml, .msg, .pst) strukturiert exportieren.")
    parser.add_argument("--input", "-i", type=Path, default=Path("."), help="Datei oder Ordner mit .eml, .msg oder .pst Dateien.")
    parser.add_argument("--output", "-o", type=Path, default=Path("out") / "mail_metadata.xlsx", help="Zieldatei: .xlsx, .csv, .parquet, .json, .xml oder .md.")
    parser.add_argument("--list-output", type=Path, help="Optionale reduzierte Review-/Microsoft-Lists-Datei: .xlsx oder .csv.")
    parser.add_argument("--markdown-dir", type=Path,
                        help="Optionaler Markdown-Datensatz: Monatsdateien nach Jahren plus index.csv/index.jsonl.")
    parser.add_argument("--log-output", type=Path, help="Optionale Logdatei. Standard: parse_log.txt neben dem Masterexport.")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE, help="Pfad zur DataFrame-Cachedatei.")
    parser.add_argument("--refresh", action="store_true", help="Cache ignorieren und alle Dateien neu parsen.")
    parser.add_argument("--hash-check", action="store_true", help="Auch unveraenderte Dateien per SHA-256 gegen den Cache pruefen. Sicherer, aber langsamer.")
    parser.add_argument("--workers", type=int, default=max(1, min(4, os.cpu_count() or 1)), help="Parallele Parser-Threads fuer neue/geaenderte Dateien.")
    parser.add_argument("--timezone", default="Europe/Berlin", help="Zeitzone fuer deutsche Datums-/Kalenderfelder.")
    parser.add_argument("--pst-backend", choices=("auto", "libpff", "outlook"), default="auto",
                        help="PST-Importer: automatisch, Outlook-unabhaengiges libpff oder klassisches Outlook.")
    return parser.parse_args()


def main() -> None:
    """Orchestriert Parsing, Cache, Masterexport und optionalen List-Export."""
    args = parse_args()
    log_path = args.log_output or default_log_path(args.output)
    configure_logging(log_path)

    started_at = datetime.now(timezone.utc)
    LOGGER.info("Start MailAnalyst")
    LOGGER.info("Input: %s", args.input.resolve())
    LOGGER.info("Output: %s", args.output.resolve())
    if args.list_output:
        LOGGER.info("List-Output: %s", args.list_output.resolve())
    if args.markdown_dir:
        LOGGER.info("Markdown-Ordner: %s", args.markdown_dir.resolve())
    LOGGER.info("Cache: %s", args.cache.resolve())
    LOGGER.info("Timezone: %s", args.timezone)
    LOGGER.info("Refresh: %s", args.refresh)
    LOGGER.info("Hash-Check: %s", args.hash_check)
    LOGGER.info("Workers: %s", args.workers)

    dataframe = build_dataframe(args.input, args.cache, args.refresh, args.hash_check, args.workers, args.timezone, args.pst_backend)
    write_output(dataframe, args.output)
    if args.list_output:
        write_output(list_export_dataframe(dataframe), args.list_output)
    if args.markdown_dir:
        write_markdown_dataset(dataframe, args.markdown_dir)

    ok_count = int((dataframe["parse_status"] == "ok").sum()) if "parse_status" in dataframe else 0
    error_count = int((dataframe["parse_status"] == "error").sum()) if "parse_status" in dataframe else 0
    elapsed_seconds = (datetime.now(timezone.utc) - started_at).total_seconds()
    LOGGER.info("Fertig: %s Dateien, %s erfolgreich, %s Fehler.", len(dataframe), ok_count, error_count)
    if error_count and {"source_path", "parse_error"}.issubset(dataframe.columns):
        for _, row in dataframe[dataframe["parse_status"] == "error"].iterrows():
            LOGGER.error("Parse-Fehler: %s | %s", row.get("source_path", ""), row.get("parse_error", ""))
    LOGGER.info("Laufzeit Sekunden: %.2f", elapsed_seconds)
    LOGGER.info("Cache: %s", args.cache.resolve())
    LOGGER.info("Export: %s", args.output.resolve())
    if args.list_output:
        LOGGER.info("List-Export: %s", args.list_output.resolve())
    if args.markdown_dir:
        LOGGER.info("Markdown-Ordner: %s", args.markdown_dir.resolve())
    LOGGER.info("Log: %s", log_path.resolve())
