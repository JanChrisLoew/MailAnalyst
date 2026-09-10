"""Select an output writer by file extension."""

from pathlib import Path
import os
import tempfile

from mailanalyst.exports.validation import validate_output
from mailanalyst.progress import report

import pandas as pd

from mailanalyst.exports.markdown import write_markdown
from mailanalyst.exports.structured import write_json, write_parquet, write_xml
from mailanalyst.exports.tabular import write_csv, write_excel


def _write_output(dataframe: pd.DataFrame, output_path: Path, markdown_link_mode: str = "full") -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()
    from mailanalyst.record_store import RecordStore
    if isinstance(dataframe, RecordStore):
        from mailanalyst.exports import batch_formats
        from mailanalyst.exports.batch_markdown import write_single
        if suffix in {".md", ".markdown"}:
            write_single(dataframe, output_path, markdown_link_mode)
        else:
            writers = {".json": batch_formats.write_json, ".csv": batch_formats.write_csv,
                       ".xlsx": batch_formats.write_excel, ".xlsm": batch_formats.write_excel,
                       ".xml": batch_formats.write_xml, ".parquet": batch_formats.write_parquet}
            if suffix not in writers:
                raise ValueError(f"Nicht unterstuetztes Ausgabeformat: {suffix}")
            writers[suffix](dataframe, output_path)
        return
    if suffix in {".md", ".markdown"}:
        write_markdown(dataframe, output_path, markdown_link_mode)
        return
    writers = {".csv": write_csv, ".xlsx": write_excel, ".xlsm": write_excel,
               ".parquet": write_parquet, ".json": write_json, ".xml": write_xml}
    if suffix not in writers:
        raise ValueError("Bitte .csv, .xlsx, .parquet, .json, .xml oder .md als Ausgabeendung verwenden.")
    writers[suffix](dataframe, output_path)


def write_output(dataframe: pd.DataFrame, output_path: Path, markdown_link_mode: str = "full") -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".pending-", suffix=output_path.suffix, dir=output_path.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        report(dataframe, "Exportieren", output_path.name)
        _write_output(dataframe, temporary, markdown_link_mode)
        report(dataframe, "Ausgaben prüfen", output_path.name)
        validate_output(temporary, len(dataframe), getattr(dataframe, "cancel", None))
        os.replace(temporary, output_path)
    finally:
        temporary.unlink(missing_ok=True)
