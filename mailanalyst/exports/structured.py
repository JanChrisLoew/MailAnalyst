"""Writers for structured master formats."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd


def write_parquet(dataframe: pd.DataFrame, output_path: Path) -> None:
    dataframe.to_parquet(output_path, index=False)


def write_json(dataframe: pd.DataFrame, output_path: Path) -> None:
    dataframe.to_json(output_path, orient="records", force_ascii=False, indent=2, date_format="iso")


def write_xml(dataframe: pd.DataFrame, output_path: Path) -> None:
    root = ET.Element("emails", count=str(len(dataframe)))
    for _, row in dataframe.iterrows():
        email_node = ET.SubElement(root, "email")
        for column, value in row.items():
            node = ET.SubElement(email_node, str(column))
            if not pd.isna(value):
                node.text = re.sub(r"[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]", "", str(value))
    ET.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)
