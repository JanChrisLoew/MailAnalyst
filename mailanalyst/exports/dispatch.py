"""Select an output writer by file extension."""

from pathlib import Path

import pandas as pd

from mailanalyst.exports.markdown import write_markdown
from mailanalyst.exports.structured import write_json, write_parquet, write_xml
from mailanalyst.exports.tabular import write_csv, write_excel


def write_output(dataframe: pd.DataFrame, output_path: Path, markdown_link_mode: str = "full") -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        write_markdown(dataframe, output_path, markdown_link_mode)
        return
    writers = {".csv": write_csv, ".xlsx": write_excel, ".xlsm": write_excel,
               ".parquet": write_parquet, ".json": write_json, ".xml": write_xml}
    if suffix not in writers:
        raise ValueError("Bitte .csv, .xlsx, .parquet, .json, .xml oder .md als Ausgabeendung verwenden.")
    writers[suffix](dataframe, output_path)
