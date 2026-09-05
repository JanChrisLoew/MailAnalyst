"""GUI-independent application operations using ordinary Python values."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

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


def check_sources(source: Path, target: Path, progress=None):
    results = run_preflight(source, progress)
    write_preflight_report(results, target)
    return results


def process_sources(options: ProcessingOptions, progress=None):
    target = options.target
    # GUI launches may inherit an unrelated, read-only working directory.
    cache_path = DEFAULT_CACHE if DEFAULT_CACHE.is_absolute() else target / DEFAULT_CACHE
    configure_logging(target / "parse_log.txt")
    with (target / "processing_options.json").open("w", encoding="utf-8") as file:
        json.dump({"input": str(options.source), "output": str(target.resolve()),
                   "output_profile": options.profile, "pst_backend": options.backend,
                   "markdown_links": options.links, "selected_sources": len(options.paths)},
                  file, ensure_ascii=False, indent=2)
    frame = build_dataframe(
        options.source, cache_path, refresh=options.refresh, hash_check=options.hash_check,
        workers=max(1, min(4, os.cpu_count() or 1)),
        pst_backend={"Automatisch": "auto", "Ohne Outlook (libpff)": "libpff",
                     "Klassisches Outlook": "outlook"}[options.backend],
        paths_override=list(options.paths), progress_callback=progress,
    )
    write_profile(frame, target, options.profile, options.links)
    return frame
