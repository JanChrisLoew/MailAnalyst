"""Export profiles shared by application services."""

from pathlib import Path

import pandas as pd

from mailanalyst.exports.dispatch import write_output
from mailanalyst.exports.markdown import write_markdown_dataset


def write_profile(frame: pd.DataFrame, target: Path, profile: str, links: str) -> None:
    link_mode = {"Vollstaendige URLs": "full", "Kompakte URLs": "compact", "Nur Linktext": "text_only"}[links]
    if profile == "Analysepaket":
        write_output(frame, target / "emails.parquet")
        write_output(frame, target / "emails.json")
        write_markdown_dataset(frame, target / "mail_workspace", link_mode)
    elif profile == "Markdown-Monatsordner":
        write_markdown_dataset(frame, target / "mail_workspace", link_mode)
    else:
        suffix = {"Parquet": ".parquet", "CSV": ".csv", "JSON": ".json", "Markdown": ".md"}[profile]
        write_output(frame, target / f"emails{suffix}", link_mode)
