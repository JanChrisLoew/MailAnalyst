"""Stream chronological months and indexes without retaining a month in RAM."""

import csv
import json

from mailanalyst.text.cells import csv_text
from mailanalyst.text.links import prepare_analysis_text

INDEX_FIELDS = ("chunk", "markdown_file", "anchor", "sent_at_utc", "sent_datetime_de", "from_email",
                "to_emails", "cc_emails", "subject", "message_id", "attachment_names", "source_path", "body_preview")


def write_message(file, row, number, mode, anchor=None):
    subject = str(row.get("subject") or "(ohne Betreff)").replace("\n", " ")
    if anchor:
        file.write(f'<a id="{anchor}"></a>\n\n')
    file.write(f"## {number}. {subject}\n\n")
    fields = [("Datum", "sent_datetime_de"), ("Von", "from_email"), ("An", "to_emails"), ("CC", "cc_emails")]
    if anchor:
        fields.append(("Message-ID", "message_id"))
    fields.append(("Anlagen", "attachment_names"))
    if anchor:
        fields.append(("PST-Ordner", "outlook_folder"))
    fields.append(("Quelle", "source_path"))
    for label, column in fields:
        value = str(row.get(column) or "").replace("\n", " ")
        if value:
            file.write(f"- **{label}:** {value}\n")
    file.write("\n### Inhalt\n\n")
    body = prepare_analysis_text(str(row.get("body_text_clean") or ""), mode)
    file.write(body.replace("\n#", "\n\\#") + "\n\n---\n\n")


def write_single(store, path, mode):
    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(f"# MailAnalyst Export\n\n{len(store)} Nachrichten\n\n")
        for number, row in enumerate(store.records(), 1):
            write_message(file, row, number, mode)


def write_dataset(store, directory, mode):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "index.jsonl").open("w", encoding="utf-8", newline="\n") as json_file, \
         (directory / "index.csv").open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=INDEX_FIELDS)
        writer.writeheader()
        for chunk, count in store.chunks():
            path = directory / (chunk[:4] if chunk != "unbekannt" else chunk) / f"{chunk}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8", newline="\n") as file:
                file.write(f"# E-Mails {chunk}\n\n{count} Nachrichten\n\n")
                for number, row in enumerate(store.records(chunk), 1):
                    anchor = f"mail-{number:05d}"
                    write_message(file, row, number, mode, anchor)
                    index = {key: row.get(key, "") for key in INDEX_FIELDS}
                    index.update(chunk=chunk, markdown_file=path.relative_to(directory).as_posix(), anchor=anchor)
                    json_file.write(json.dumps(index, ensure_ascii=False, allow_nan=False) + "\n")
                    writer.writerow({key: csv_text(value) for key, value in index.items()})
