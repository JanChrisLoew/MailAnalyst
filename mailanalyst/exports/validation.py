"""Read back exports and check counts and portable Markdown references."""

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd


def validate_output(path: Path, count: int) -> None:
    suffix = path.suffix.lower()
    if suffix == ".json":
        actual = len(json.loads(path.read_text(encoding="utf-8")))
    elif suffix == ".parquet":
        actual = len(pd.read_parquet(path))
    elif suffix in {".xlsx", ".xlsm"}:
        actual = len(pd.read_excel(path))
    elif suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as file:
            actual = max(0, sum(1 for _ in csv.reader(file)) - 1)
    elif suffix == ".xml":
        actual = len(ET.parse(path).getroot().findall("email"))
    elif suffix in {".md", ".markdown"}:
        text = path.read_text(encoding="utf-8")
        if not text.startswith(f"# MailAnalyst Export\n\n{count} Nachrichten\n"):
            raise ValueError(f"Invalid Markdown export: {path}")
        return
    else:
        raise ValueError(f"Unsupported validation format: {suffix}")
    if actual != count:
        raise ValueError(f"Export count mismatch: {path}: {actual} != {count}")


def validate_dataset(directory: Path, count: int) -> None:
    rows = [json.loads(line) for line in (directory / "index.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != count:
        raise ValueError("Markdown index count mismatch")
    validate_output(directory / "index.csv", count)
    for row in rows:
        path = (directory / row["markdown_file"]).resolve()
        if not path.is_relative_to(directory.resolve()):
            raise ValueError("Markdown reference leaves dataset")
        if f'<a id="{row["anchor"]}"></a>' not in path.read_text(encoding="utf-8"):
            raise ValueError("Missing Markdown anchor")
