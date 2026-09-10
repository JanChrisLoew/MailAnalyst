"""GUI-independent application operations using ordinary Python values."""

import json
import os
from dataclasses import dataclass, replace
from pathlib import Path

from mailanalyst.cancellation import Cancellation, Cancelled, check_cancel
from mailanalyst.checks.preflight import run_preflight, write_preflight_report, check_file
from mailanalyst.checks.targets import (check_locations, check_components, require_usable,
                                      profile_formats, validate_source_target)
from mailanalyst.checks.system import write_system_check_report
from mailanalyst.config import DEFAULT_CACHE
from mailanalyst.exports.profiles import write_profile
from mailanalyst.logging_setup import configure_logging
from mailanalyst.batch_pipeline import build_store


@dataclass(frozen=True)
class ProcessingOptions:
    source: Path
    target: Path
    paths: tuple[Path, ...]
    profile: str
    backend: str
    links: str
    refresh: bool = False
    hash_check: bool = False
    preflight: tuple | None = None


def check_sources(source: Path, target: Path, progress=None, cancel=None):
    check_cancel(cancel)
    validate_source_target(source, target)
    require_usable(check_locations([target]))
    results = run_preflight(source, progress, excluded=(target,), cancel=cancel)
    check_cancel(cancel)
    write_preflight_report(results, target)
    return results


def process_sources(options: ProcessingOptions, progress=None, cancel=None, phase_progress=None):
    cancel = cancel or Cancellation()
    from mailanalyst.progress import PhaseReporter
    from mailanalyst.review_store import write_review
    phases = PhaseReporter(phase_progress)
    from mailanalyst.runs import Run
    from mailanalyst.exports.validation import validate_dataset
    from mailanalyst.config import LOGGER

    target = options.target
    cache_path = DEFAULT_CACHE if DEFAULT_CACHE.is_absolute() else target / DEFAULT_CACHE
    validate_source_target(options.source, target, options.paths, cache_path)
    saved = {"input": str(options.source.resolve()), "output": str(target.resolve()),
             "output_profile": options.profile, "pst_backend": options.backend,
             "markdown_links": options.links, "selected_sources": [str(path.resolve()) for path in options.paths],
             "refresh": options.refresh, "hash_check": options.hash_check, "timezone": "Europe/Berlin",
             "preflight_binding": "sha256"}
    run = Run(target, saved)
    store = None
    try:
        configure_logging(run.root / "parse_log.txt")
        cancel.check()
        LOGGER.info("Start MailAnalyst: %s | Optionen: %s", run.root.name, saved)
        selection = list(options.preflight) if options.preflight is not None else [check_file(p, cancel) for p in options.paths]
        selected_keys = {str(p.resolve()) for p in options.paths}
        selection = [replace(row, include=str(Path(row.path).resolve()) in selected_keys) for row in selection]
        by_path = {str(Path(row.path).resolve()): row for row in selection}
        if any(str(p.resolve()) not in by_path for p in options.paths):
            raise ValueError("Auswahl nicht vollstaendig vorgeprueft; erneut pruefen")
        guards = {str(p.resolve()): (by_path[str(p.resolve())].size, by_path[str(p.resolve())].modified_at_ns,
                                    by_path[str(p.resolve())].sha256) for p in options.paths}
        if any(by_path[str(p.resolve())].status == "ignored" for p in options.paths):
            raise ValueError("Nicht unterstuetzte Dateien koennen nicht verarbeitet werden")
        write_preflight_report(selection, run.root)
        checks = check_components(options.paths, profile_formats(options.profile),
                                  {"Automatisch": "auto", "Ohne Outlook (libpff)": "libpff",
                                   "Klassisches Outlook": "outlook"}[options.backend])
        checks += check_locations([run.root, cache_path.parent], sum(by_path[str(p.resolve())].size for p in options.paths))
        write_system_check_report(checks, run.root)
        require_usable(checks)
        for row in checks:
            if row.status == "warning":
                LOGGER.warning("%s: %s", row.name, row.detail)
        (run.root / "processing_options.json").write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
        store = build_store(
            options.source, cache_path, run.root / "work.sqlite3", refresh=options.refresh, hash_check=options.hash_check,
            workers=max(1, min(4, os.cpu_count() or 1)),
            pst_backend={"Automatisch": "auto", "Ohne Outlook (libpff)": "libpff",
                         "Klassisches Outlook": "outlook"}[options.backend],
            paths_override=list(options.paths), progress_callback=progress, cancel=cancel, phase_progress=phases,
            preflight=guards,
        )
        store.phase_progress = phases
        phases("Lauf dokumentieren", "Quellenprüfung schreiben", len(store))
        run.record_store(store)
        write_profile(store, run.pending, options.profile, options.links, cancel=cancel)
        if (run.pending / "mail_workspace").exists():
            phases("Ausgaben prüfen", "Markdown-Index und Verweise", len(store))
            validate_dataset(run.pending / "mail_workspace", len(store), cancel)
        phases("Ergebnis vorbereiten", "Blätterbaren Ergebnisindex erstellen", len(store))
        write_review(store, run.pending / "review.sqlite3")
        frame = store.preview()
        phases("Abschließen", "Exporthashes und Laufpaket fertigstellen", len(store))
        cancel.begin_commit()
        run.publish()
        run.finish()
        frame.attrs["run_directory"] = str(run.root)
        return frame
    except Cancelled as exc:
        run.fail(exc, status="cancelled")
        raise Cancelled(f"Abgebrochen. Laufdetails: {run.root}") from exc
    except Exception as exc:
        run.fail(exc)
        raise RuntimeError(f"{exc} (Laufdetails: {run.root})") from exc

    finally:
        if store is not None:
            store.close()
            store.path.unlink(missing_ok=True)
