from __future__ import annotations
from pathlib import Path
import pandas as pd
from mailanalyst.exports.tabular import write_csv
from mailanalyst.text.links import prepare_analysis_text
from mailanalyst.exports.markdown_safety import inline_text, quoted_body


def write_markdown_dataset(dataframe: pd.DataFrame, output_dir: Path, link_mode: str = "full") -> None:
    """Schreibt chronologische Monatsdateien plus maschinenlesbaren Suchindex."""
    from mailanalyst.record_store import RecordStore
    if isinstance(dataframe, RecordStore):
        from mailanalyst.exports.batch_markdown import write_dataset
        from mailanalyst.progress import report
        report(dataframe, "Exportieren", "Markdown-Monatsordner")
        write_dataset(dataframe, output_dir, link_mode)
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    data = dataframe.copy()
    if "sent_at_utc" in data.columns:
        parsed_dates = pd.to_datetime(data["sent_at_utc"], errors="coerce", utc=True)
    else:
        parsed_dates = pd.Series(pd.NaT, index=data.index, dtype="datetime64[ns, UTC]")
    data["_chunk"] = parsed_dates.dt.strftime("%Y-%m").fillna("unbekannt")
    data["_sort_date"] = parsed_dates
    data = data.sort_values(["_sort_date"] + (["subject"] if "subject" in data else []), na_position="last")

    index_rows: list[dict[str, object]] = []
    for chunk, group in data.groupby("_chunk", sort=True):
        year = chunk[:4] if chunk != "unbekannt" else "unbekannt"
        chunk_dir = output_dir / year
        chunk_dir.mkdir(parents=True, exist_ok=True)
        chunk_path = chunk_dir / f"{chunk}.md"
        with chunk_path.open("w", encoding="utf-8", newline="\n") as file:
            file.write(f"# E-Mails {chunk}\n\n{len(group)} Nachrichten\n\n")
            for number, (_, row) in enumerate(group.iterrows(), start=1):
                anchor = f"mail-{number:05d}"
                subject = inline_text(row.get("subject", ""), "(ohne Betreff)")
                file.write(f"<a id=\"{anchor}\"></a>\n\n## {number}. {subject}\n\n")
                metadata = (
                    ("Datum", "sent_datetime_de"), ("Von", "from_email"), ("An", "to_emails"),
                    ("CC", "cc_emails"), ("Message-ID", "message_id"), ("Anlagen", "attachment_names"),
                    ("PST-Ordner", "outlook_folder"), ("Quelle", "source_path"),
                )
                for label, column in metadata:
                    value = inline_text(row.get(column, ""))
                    if value and value.lower() != "nan":
                        file.write(f"- **{label}:** {value}\n")
                file.write("\n### Inhalt\n\n")
                body = prepare_analysis_text(str(row.get("body_text_clean", "") or ""), link_mode)
                file.write(quoted_body(body) + "\n\n---\n\n")
                index_rows.append({
                    "chunk": chunk,
                    "markdown_file": chunk_path.relative_to(output_dir).as_posix(),
                    "anchor": anchor,
                    "sent_at_utc": row.get("sent_at_utc", ""),
                    "sent_datetime_de": row.get("sent_datetime_de", ""),
                    "from_email": row.get("from_email", ""),
                    "to_emails": row.get("to_emails", ""),
                    "cc_emails": row.get("cc_emails", ""),
                    "subject": row.get("subject", ""),
                    "message_id": row.get("message_id", ""),
                    "attachment_names": row.get("attachment_names", ""),
                    "source_path": row.get("source_path", ""),
                    "body_preview": row.get("body_preview", ""),
                })

    index_frame = pd.DataFrame(index_rows)
    index_frame.to_json(output_dir / "index.jsonl", orient="records", lines=True, force_ascii=False, date_format="iso")
    write_csv(index_frame, output_dir / "index.csv")


def write_markdown(dataframe: pd.DataFrame, output_path: Path, markdown_link_mode: str = "full") -> None:
    with output_path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(f"# MailAnalyst Export\n\n{len(dataframe)} Nachrichten\n\n")
        for number, (_, row) in enumerate(dataframe.iterrows(), start=1):
            subject = inline_text(row.get("subject", ""), "(ohne Betreff)")
            file.write(f"## {number}. {subject}\n\n")
            for label, column in (("Datum", "sent_datetime_de"), ("Von", "from_email"),
                                  ("An", "to_emails"), ("CC", "cc_emails"),
                                  ("Anlagen", "attachment_names"), ("Quelle", "source_path")):
                value = inline_text(row.get(column, ""))
                if value:
                    file.write(f"- **{label}:** {value}\n")
            file.write("\n### Inhalt\n\n")
            body = prepare_analysis_text(str(row.get("body_text_clean", "") or ""), markdown_link_mode)
            file.write(quoted_body(body) + "\n\n---\n\n")
