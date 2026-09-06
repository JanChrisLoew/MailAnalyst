"""GUI-independent application operations using ordinary Python values."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from mailanalyst.cancellation import Cancellation, Cancelled, check_cancel
from mailanalyst.checks.preflight import run_preflight, write_preflight_report
from mailanalyst.config import DEFAULT_CACHE
from mailanalyst.exports.profiles import write_profile
from mailanalyst.logging_setup import configure_logging
from mailanalyst.pipeline import build_dataframe


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


def check_sources(source: Path, target: Path, progress=None, cancel=None):
    check_cancel(cancel)
    results = run_preflight(source, progress)
    check_cancel(cancel)
    write_preflight_report(results, target)
    return results


def process_sources(options: ProcessingOptions, progress=None, cancel=None):
    cancel = cancel or Cancellation()
    from mailanalyst.runs import Run
    from mailanalyst.exports.validation import validate_dataset
    from mailanalyst.config import LOGGER

    target = options.target
    cache_path = DEFAULT_CACHE if DEFAULT_CACHE.is_absolute() else target / DEFAULT_CACHE
    saved = {"input": str(options.source.resolve()), "output": str(target.resolve()),
             "output_profile": options.profile, "pst_backend": options.backend,
             "markdown_links": options.links, "selected_sources": [str(path.resolve()) for path in options.paths],
             "refresh": options.refresh, "hash_check": options.hash_check, "timezone": "Europe/Berlin"}
    run = Run(target, saved)
    try:
        configure_logging(run.root / "parse_log.txt")
        cancel.check()
        LOGGER.info("Start MailAnalyst: %s | Optionen: %s", run.root.name, saved)
        (run.root / "processing_options.json").write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
        frame = build_dataframe(
            options.source, cache_path, refresh=options.refresh, hash_check=options.hash_check,
            workers=max(1, min(4, os.cpu_count() or 1)),
            pst_backend={"Automatisch": "auto", "Ohne Outlook (libpff)": "libpff",
                         "Klassisches Outlook": "outlook"}[options.backend],
            paths_override=list(options.paths), progress_callback=progress, cancel=cancel,
        )
        run.record_frame(frame)
        write_profile(frame, run.pending, options.profile, options.links, cancel=cancel)
        if (run.pending / "mail_workspace").exists():
            validate_dataset(run.pending / "mail_workspace", len(frame))
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
