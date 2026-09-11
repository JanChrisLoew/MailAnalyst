"""Incremental master writers for the disk-backed record store."""

import csv
import json
import re
from xml.sax.saxutils import escape

import pyarrow as pa
import pyarrow.parquet as pq
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell

from mailanalyst.text.cells import csv_text


def write_json(store, path):
    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write("[\n")
        separator = ""
        for row in store.records():
            file.write(separator + json.dumps(row, ensure_ascii=False, allow_nan=False))
            separator = ",\n"
        file.write("\n]\n")


def write_csv(store, path):
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([csv_text(key) for key in store.columns])
        for row in store.records():
            writer.writerow([csv_text(row.get(key)) for key in store.columns])


def write_excel(store, path):
    if len(store) > 1048575:
        raise ValueError("Excel-Blattgrenze ueberschritten; JSON oder Parquet verwenden")
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("Sheet1")

    def append(values):
        cells = []
        for value in values:
            cell = WriteOnlyCell(sheet, value=value[:32767] if isinstance(value, str) else value)
            if isinstance(value, str):
                cell.data_type = "s"
            cells.append(cell)
        sheet.append(cells)

    try:
        append(store.columns)
        for row in store.records():
            append(row.get(key) for key in store.columns)
        workbook.save(path)
    finally:
        workbook.close()


def write_parquet(store, path):
    fields = []
    for key, types in store.columns.items():
        kind = pa.int64() if types == {"int"} else pa.bool_() if types == {"bool"} else pa.string()
        if types and types <= {"int", "float"} and "float" in types:
            kind = pa.float64()
        fields.append(pa.field(key, kind))
    schema = pa.schema(fields)
    with pq.ParquetWriter(path, schema) as writer:
        for rows in store.batches():
            for row in rows:
                for field in schema:
                    if pa.types.is_string(field.type) and row[field.name] is not None:
                        row[field.name] = str(row[field.name])
            writer.write_table(pa.Table.from_pylist(rows, schema=schema))


def write_xml(store, path):
    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(f'<?xml version="1.0" encoding="utf-8"?>\n<emails count="{len(store)}">')
        for row in store.records():
            file.write("<email>")
            for key, value in row.items():
                text = "" if value is None else re.sub(
                    r"[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]", "", str(value))
                file.write(f"<{key}>{escape(text)}</{key}>")
            file.write("</email>")
        file.write("</emails>")
