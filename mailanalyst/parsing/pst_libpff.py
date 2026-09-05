from __future__ import annotations
from pathlib import Path
from datetime import datetime
from datetime import timezone
from mailanalyst.config import CACHE_SCHEMA_VERSION
from mailanalyst.models import FileSignature
from mailanalyst.text.cleaning import clean_plain_text
from mailanalyst.text.dates import derive_date_fields
from mailanalyst.text.html import html_to_text
from mailanalyst.text.dates import parse_datetime
from mailanalyst.hashing import sha256_file


def parse_pst_libpff(path: Path, signature: FileSignature, timezone_name: str) -> list[dict[str, object]]:
    """Liest eine PST direkt mit pypff, ohne Outlook zu starten."""
    try:
        import pypff
    except ImportError as exc:
        raise RuntimeError("libpff/pypff ist nicht installiert. Bitte Backend 'Outlook' waehlen oder pypff installieren.") from exc

    def attr(item: object, *names: str, default: object = "") -> object:
        for name in names:
            try:
                value = getattr(item, name)
                return value() if callable(value) else value
            except Exception:
                continue
        return default

    def text_value(value: object) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value or "")

    rows: list[dict[str, object]] = []
    pst_file = pypff.open(str(path.resolve()))

    def walk(folder: object, parent: str = "") -> None:
        folder_name = text_value(attr(folder, "name", "display_name", "get_name", default="Ordner"))
        folder_path = f"{parent}\\{folder_name}" if parent else folder_name
        messages = attr(folder, "sub_messages", default=[])
        for index, message in enumerate(messages or []):
            identifier = text_value(attr(message, "identifier", "get_identifier", default=index))
            try:
                sent_value = attr(message, "client_submit_time", "delivery_time", default="")
                if isinstance(sent_value, datetime):
                    if sent_value.tzinfo is None:
                        sent_value = sent_value.replace(tzinfo=timezone.utc)
                    sent_at, sent_at_utc = sent_value.isoformat(), sent_value.astimezone(timezone.utc).isoformat()
                else:
                    sent_at, sent_at_utc = parse_datetime(text_value(sent_value))
                body_raw = text_value(attr(message, "plain_text_body", "get_plain_text_body"))
                body_html = text_value(attr(message, "html_body", "get_html_body"))
                body_clean = clean_plain_text(body_raw) or html_to_text(body_html)
                attachments = attr(message, "attachments", default=[]) or []
                attachment_names = [text_value(attr(item, "name", "long_filename", "short_filename", default=""))
                                    for item in attachments]
                rows.append({
                    "source_path": f"{path.resolve()}::{folder_path}::{identifier}",
                    "source_file_path": str(path.resolve()), "archive_path": str(path.resolve()),
                    "outlook_folder": folder_path, "outlook_entry_id": identifier,
                    "pst_backend": "libpff", "message_id": text_value(attr(message, "internet_message_identifier")),
                    "in_reply_to": "", "references": "", "subject": text_value(attr(message, "subject")),
                    "sent_at": sent_at, "sent_at_utc": sent_at_utc, **derive_date_fields(sent_at_utc, timezone_name),
                    "from_name": text_value(attr(message, "sender_name")),
                    "from_email": text_value(attr(message, "sender_email_address")),
                    "to": text_value(attr(message, "display_to")), "to_emails": text_value(attr(message, "display_to")),
                    "cc": text_value(attr(message, "display_cc")), "cc_emails": text_value(attr(message, "display_cc")),
                    "bcc": text_value(attr(message, "display_bcc")), "bcc_emails": text_value(attr(message, "display_bcc")),
                    "reply_to": "", "reply_to_emails": "", "body_text": body_clean,
                    "body_text_raw": body_raw, "body_text_clean": body_clean,
                    "body_text_length": len(body_clean), "body_text_raw_length": len(body_raw),
                    "body_preview": body_clean[:500], "body_html": body_html, "body_html_length": len(body_html),
                    "has_attachments": bool(attachment_names), "attachment_count": len(attachment_names),
                    "attachment_names": "; ".join(name for name in attachment_names if name),
                    "mime_defects": "", "parse_status": "ok", "parse_error": "",
                })
            except Exception as exc:
                rows.append({"source_path": f"{path.resolve()}::{folder_path}::{identifier}",
                             "source_file_path": str(path.resolve()), "archive_path": str(path.resolve()),
                             "outlook_folder": folder_path, "outlook_entry_id": identifier, "pst_backend": "libpff",
                             "parse_status": "error", "parse_error": str(exc)})
        for child in (attr(folder, "sub_folders", default=[]) or []):
            walk(child, folder_path)

    try:
        walk(pst_file.get_root_folder())
    finally:
        pst_file.close()
    base = signature.__dict__.copy()
    base["cache_schema_version"] = CACHE_SCHEMA_VERSION
    if not base["file_sha256"]:
        base["file_sha256"] = sha256_file(path)
    for row in rows:
        row.update({key: value for key, value in base.items() if key != "source_path"})
    return rows
