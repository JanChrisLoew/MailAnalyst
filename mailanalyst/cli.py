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
    """Create a run package and retain explicit CLI output paths as copies."""
    from mailanalyst.runs import Run
    from mailanalyst.legacy_outputs import publish_copy
    from mailanalyst.exports.validation import validate_dataset

    from mailanalyst.cli_paths import validate_paths

    args = parse_args()
    validate_paths(args)
    saved = {key: str(value.resolve()) if isinstance(value, Path) else value for key, value in vars(args).items()}
    run = Run(args.output.parent, saved)
    try:
        configure_logging(run.root / "parse_log.txt")
        LOGGER.info("Start MailAnalyst: %s | Optionen: %s", run.root.name, saved)
        dataframe = build_dataframe(args.input, args.cache, args.refresh, args.hash_check,
                                    args.workers, args.timezone, args.pst_backend)
        run.record_frame(dataframe)
        exports = [(run.pending / "master" / args.output.name, args.output)]
        write_output(dataframe, exports[0][0])
        if args.list_output:
            path = run.pending / "list" / args.list_output.name
            write_output(list_export_dataframe(dataframe), path)
            exports.append((path, args.list_output))
        if args.markdown_dir:
            path = run.pending / "mail_workspace"
            write_markdown_dataset(dataframe, path)
            validate_dataset(path, len(dataframe))
            exports.append((path, args.markdown_dir))
        relative = [(path.relative_to(run.pending), target) for path, target in exports]
        run.publish()
        for path, target in relative:
            publish_copy(run.root / "exports" / path, target)
        LOGGER.info("Fertig: %s Nachrichten, %s Parserfehler. Laufpaket: %s",
                    len(dataframe), run.data["parser_errors"], run.root)
        for handler in LOGGER.handlers:
            handler.flush()
        publish_copy(run.root / "parse_log.txt", args.log_output or default_log_path(args.output))
        run.finish()
    except Exception as exc:
        run.fail(exc)
        raise RuntimeError(f"{exc} (Laufdetails: {run.root})") from exc
