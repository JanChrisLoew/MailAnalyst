"""Synthetic batch benchmark; run with python -m scripts.benchmark_batches."""

import argparse
import ctypes
from ctypes import wintypes
import json
import logging
import os
from pathlib import Path
import platform
import time
from unittest.mock import patch

from mailanalyst.batch_pipeline import build_store
from mailanalyst.config import LOGGER
from mailanalyst.exports.profiles import write_profile
from mailanalyst.exports.validation import validate_dataset
from mailanalyst.hashing import file_signature
from mailanalyst.parsing.dispatch import parse_mail_file
from mailanalyst.runs import Run


def peak_memory_mib():
    if os.name != "nt":
        return None

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
            "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return round(counters.PeakWorkingSetSize / 1048576, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--mode", choices=("eml", "archive-double"), required=True)
    parser.add_argument("--output", type=Path, required=True, help="New, unused directory for synthetic data")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("count must be positive")
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    source = root / "input"
    source.mkdir()
    LOGGER.setLevel(logging.WARNING)
    body = "Synthetic benchmark content. " * 80
    template = ("From: Sender <sender@example.test>\nTo: Reader <reader@example.test>\n"
                "Subject: Synthetic batch message\nDate: Tue, 01 Sep 2026 12:00:00 +0000\n"
                "Message-ID: <NUMBER@example.test>\nContent-Type: text/plain; charset=utf-8\n\n" + body).encode()
    generated = time.perf_counter()
    if args.mode == "eml":
        for i in range(args.count):
            (source / f"{i:06d}.eml").write_bytes(template.replace(b"NUMBER", str(i).encode()))
        context = patch.dict({}, {})
    else:
        seed = root / "seed.eml"
        seed.write_bytes(template)
        sample = parse_mail_file(seed, file_signature(seed, include_hash=True), "Europe/Berlin")[0]
        archive = source / "synthetic.pst"
        archive.write_bytes(b"Synthetic placeholder; no PST importer is exercised")

        def rows(path, signature, *_):
            for i in range(args.count):
                yield {**sample, **signature.__dict__, "source_file_path": signature.key,
                       "source_path": f"{signature.key}::Synthetic::{i}", "archive_path": signature.key,
                       "message_id": f"<{i}@example.test>", "pst_backend": "libpff"}

        context = patch("mailanalyst.batch_sources.iter_mail_file", side_effect=rows)
    result = {"mode": args.mode, "count": args.count, "python": platform.python_version(),
              "generation_seconds": round(time.perf_counter() - generated, 2), "passes": []}
    with context:
        for label in ("fresh", "cached"):
            start = time.perf_counter()
            run = Run(root, {"synthetic_benchmark": args.mode, "count": args.count})
            store = build_store(source, root / "cache.sqlite3", run.root / "work.sqlite3", workers=4, pst_backend="libpff")
            imported = time.perf_counter()
            try:
                run.record_store(store)
                write_profile(store, run.pending, "Analysepaket", "Vollstaendige URLs")
                validate_dataset(run.pending / "mail_workspace", len(store))
                preview = store.preview()
                assert len(store) == args.count and len(preview) <= 500
                assert store.errors == 0 and store.max_batch_rows <= 500
                run.publish()
                run.finish()
                result["passes"].append({"pass": label, "seconds": round(time.perf_counter() - start, 2),
                    "import_seconds": round(imported - start, 2), "peak_working_set_mib": peak_memory_mib(),
                    "messages": len(store), "cache_hits": run.data["cache_hits"],
                    "max_batch_rows": store.max_batch_rows, "max_batch_bytes": store.max_batch_bytes})
                print(json.dumps(result["passes"][-1]), flush=True)
            finally:
                store.close()
                store.path.unlink(missing_ok=True)
    (root / "benchmark.json").write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
