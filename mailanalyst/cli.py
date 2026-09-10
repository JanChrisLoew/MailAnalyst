from __future__ import annotations
from pathlib import Path
import argparse
from datetime import datetime
import os
from datetime import timezone
from mailanalyst.config import DEFAULT_CACHE
from mailanalyst.config import LOGGER
from mailanalyst.batch_pipeline import build_store
from mailanalyst.logging_setup import configure_logging
from mailanalyst.logging_setup import default_log_path
from mailanalyst.exports.list_view import ListView
from mailanalyst.exports.markdown import write_markdown_dataset
from mailanalyst.exports.dispatch import write_output
from mailanalyst.version import APP_VERSION


def parse_args() -> argparse.Namespace:
    """Definiert die Kommandozeilenoptionen fuer den Batchlauf."""
    parser = argparse.ArgumentParser(description="Outlook-Dateien (.eml, .msg, .pst) strukturiert exportieren.")
    parser.add_argument("--version", action="version", version=f"MailAnalyst {APP_VERSION}")
    parser.add_argument("--input", "-i", type=Path, default=Path("."), help="Datei oder Ordner mit .eml, .msg oder .pst Dateien.")
    parser.add_argument("--output", "-o", type=Path, default=Path("out") / "mail_metadata.xlsx", help="Zieldatei: .xlsx, .csv, .parquet, .json, .xml oder .md.")
    parser.add_argument("--list-output", type=Path, help="Optionale reduzierte Review-/Microsoft-Lists-Datei: .xlsx oder .csv.")
    parser.add_argument("--markdown-dir", type=Path,
                        help="Optionaler Markdown-Datensatz: Monatsdateien nach Jahren plus index.csv/index.jsonl.")
    parser.add_argument("--log-output", type=Path, help="Optionale Logdatei. Standard: parse_log.txt neben dem Masterexport.")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE, help="Pfad zum SQLite-Cache.")
    parser.add_argument("--refresh", action="store_true", help="Cache ignorieren und alle Dateien neu parsen.")
    parser.add_argument("--hash-check", action="store_true", help="Kompatibilitaetsoption; CLI-Quellen werden stets per SHA-256 an die Vorpruefung gebunden.")
    parser.add_argument("--batch-size", type=int, default=500, help="Nachrichten pro Batch (1 bis 5000).")
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
    saved["preflight_binding"] = "sha256"
    run = Run(args.output.parent, saved)
    dataframe = None
    try:
        configure_logging(run.root / "parse_log.txt")
        LOGGER.info("Start MailAnalyst: %s | Optionen: %s", run.root.name, saved)
        from mailanalyst.discovery import discover_mail_files
        from mailanalyst.checks.preflight import check_file, write_preflight_report
        from mailanalyst.checks.targets import check_components, check_locations, require_usable
        from mailanalyst.checks.system import write_system_check_report
        paths = discover_mail_files(args.input)
        selection = [check_file(path) for path in paths]
        write_preflight_report(selection, run.root)
        locations = [run.root, args.cache.parent, args.output.parent,
                     (args.log_output or default_log_path(args.output)).parent]
        formats = {args.output.suffix.lower()}
        if args.list_output:
            locations.append(args.list_output.parent)
            formats.add(args.list_output.suffix.lower())
        if args.markdown_dir:
            locations.append(args.markdown_dir.parent)
        checks = check_components(paths, formats, args.pst_backend)
        checks += check_locations(locations, sum(row.size for row in selection))
        write_system_check_report(checks, run.root)
        require_usable(checks)
        for row in checks:
            if row.status == "warning":
                LOGGER.warning("%s: %s", row.name, row.detail)
        guards = {row.path: (row.size, row.modified_at_ns, row.sha256) for row in selection}
        dataframe = build_store(args.input, args.cache, run.root / "work.sqlite3", args.refresh, args.hash_check,
                                args.workers, args.timezone, args.pst_backend, batch_size=args.batch_size,
                                paths_override=paths, preflight=guards)
        run.record_store(dataframe)
        exports = [(run.pending / "master" / args.output.name, args.output)]
        write_output(dataframe, exports[0][0])
        if args.list_output:
            path = run.pending / "list" / args.list_output.name
            write_output(ListView(dataframe), path)
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

    finally:
        if dataframe is not None:
            dataframe.close()
            dataframe.path.unlink(missing_ok=True)
