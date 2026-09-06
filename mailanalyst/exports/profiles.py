"""Export profiles shared by application services."""

from pathlib import Path

import pandas as pd

from mailanalyst.cancellation import check_cancel
from mailanalyst.exports.dispatch import write_output
from mailanalyst.exports.markdown import write_markdown_dataset


def write_profile(frame: pd.DataFrame, target: Path, profile: str, links: str, cancel=None) -> None:
    link_mode = {"Vollstaendige URLs": "full", "Kompakte URLs": "compact", "Nur Linktext": "text_only"}[links]
    if profile == "Analysepaket":
        check_cancel(cancel)
        write_output(frame, target / "emails.parquet")
        check_cancel(cancel)
        write_output(frame, target / "emails.json")
        check_cancel(cancel)
        write_markdown_dataset(frame, target / "mail_workspace", link_mode)
    elif profile == "Markdown-Monatsordner":
        check_cancel(cancel)
        write_markdown_dataset(frame, target / "mail_workspace", link_mode)
    else:
        suffix = {"Parquet": ".parquet", "CSV": ".csv", "JSON": ".json", "Markdown": ".md"}[profile]
        check_cancel(cancel)
        write_output(frame, target / f"emails{suffix}", link_mode)
    check_cancel(cancel)
