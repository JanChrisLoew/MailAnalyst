from __future__ import annotations
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime
from datetime import timezone
from mailanalyst.config import CACHE_SCHEMA_VERSION
from mailanalyst.models import FileSignature
from mailanalyst.text.cleaning import clean_plain_text
from mailanalyst.text.dates import derive_date_fields
from mailanalyst.text.addresses import format_address_emails
from mailanalyst.text.html import html_to_text
from mailanalyst.text.dates import parse_datetime
from mailanalyst.hashing import sha256_file


def outlook_mail_row(item: object, pst_path: Path, folder_path: str, timezone_name: str) -> dict[str, object]:
    """Uebertraegt ein Outlook-MailItem aus einer PST in das gemeinsame Schema."""
    def value(name: str, default: object = "") -> object:
        try:
            return getattr(item, name)
        except Exception:
            return default

    sent_value = value("SentOn", "")
    if isinstance(sent_value, datetime):
        if sent_value.tzinfo is None:
            sent_value = sent_value.replace(tzinfo=ZoneInfo(timezone_name))
        sent_at = sent_value.isoformat()
        sent_at_utc = sent_value.astimezone(timezone.utc).isoformat()
    else:
        sent_at, sent_at_utc = parse_datetime(str(sent_value or ""))
    sender_name = str(value("SenderName", "") or "")
    sender_email = str(value("SenderEmailAddress", "") or "")
    body_raw = str(value("Body", "") or "")
    body_html = str(value("HTMLBody", "") or "")
    body_clean = clean_plain_text(body_raw) or html_to_text(body_html)
    attachment_names: list[str] = []
    try:
        attachments = item.Attachments
        attachment_names = [str(attachments.Item(index).FileName or "") for index in range(1, attachments.Count + 1)]
    except Exception:
        pass
    entry_id = str(value("EntryID", "") or "")
    return {
        "source_path": f"{pst_path.resolve()}::{folder_path}::{entry_id}",
        "source_file_path": str(pst_path.resolve()),
        "archive_path": str(pst_path.resolve()),
        "outlook_folder": folder_path,
        "outlook_entry_id": entry_id,
        "message_id": str(value("InternetMessageID", "") or ""),
        "in_reply_to": "",
        "references": "",
        "subject": str(value("Subject", "") or ""),
        "sent_at": sent_at,
        "sent_at_utc": sent_at_utc,
        **derive_date_fields(sent_at_utc, timezone_name),
        "from_name": sender_name,
        "from_email": sender_email,
        "to": str(value("To", "") or ""),
        "to_emails": format_address_emails([str(value("To", "") or "")]),
        "cc": str(value("CC", "") or ""),
        "cc_emails": format_address_emails([str(value("CC", "") or "")]),
        "bcc": str(value("BCC", "") or ""),
        "bcc_emails": format_address_emails([str(value("BCC", "") or "")]),
        "reply_to": "",
        "reply_to_emails": "",
        "body_text": body_clean,
        "body_text_raw": body_raw,
        "body_text_clean": body_clean,
        "body_text_length": len(body_clean),
        "body_text_raw_length": len(body_raw),
        "body_preview": body_clean[:500],
        "body_html": body_html,
        "body_html_length": len(body_html),
        "has_attachments": bool(attachment_names),
        "attachment_count": len(attachment_names),
        "attachment_names": "; ".join(attachment_names),
        "mime_defects": "",
        "parse_status": "ok",
        "parse_error": "",
    }


def parse_pst_outlook(path: Path, signature: FileSignature, timezone_name: str) -> list[dict[str, object]]:
    """Liest MailItems einer PST ueber klassisches Outlook unter Windows."""
    try:
        import win32com.client
        import pythoncom
    except ImportError as exc:
        raise RuntimeError("PST-Unterstuetzung fehlt. Bitte pywin32 installieren.") from exc

    pythoncom.CoInitialize()
    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    before = {str(store.FilePath).lower() for store in namespace.Stores if getattr(store, "FilePath", "")}
    namespace.AddStoreEx(str(path.resolve()), 3)
    store = next((candidate for candidate in namespace.Stores
                  if str(getattr(candidate, "FilePath", "")).lower() == str(path.resolve()).lower()), None)
    if store is None:
        raise RuntimeError(f"Outlook konnte die PST nicht oeffnen: {path}")
    root = store.GetRootFolder()
    rows: list[dict[str, object]] = []

    def walk(folder: object, parent: str = "") -> None:
        folder_path = f"{parent}\\{folder.Name}" if parent else str(folder.Name)
        for index in range(1, folder.Items.Count + 1):
            item = folder.Items.Item(index)
            if int(getattr(item, "Class", 0)) == 43:  # olMail
                try:
                    rows.append(outlook_mail_row(item, path, folder_path, timezone_name))
                except Exception as exc:
                    entry_id = str(getattr(item, "EntryID", "") or "")
                    rows.append({
                        "source_path": f"{path.resolve()}::{folder_path}::{entry_id}",
                        "source_file_path": str(path.resolve()),
                        "archive_path": str(path.resolve()),
                        "outlook_folder": folder_path,
                        "outlook_entry_id": entry_id,
                        "subject": str(getattr(item, "Subject", "") or ""),
                        "parse_status": "error",
                        "parse_error": str(exc),
                    })
        for index in range(1, folder.Folders.Count + 1):
            walk(folder.Folders.Item(index), folder_path)

    try:
        walk(root)
    finally:
        if str(path.resolve()).lower() not in before:
            namespace.RemoveStore(root)
        pythoncom.CoUninitialize()
    base = signature.__dict__.copy()
    base["cache_schema_version"] = CACHE_SCHEMA_VERSION
    if not base["file_sha256"]:
        base["file_sha256"] = sha256_file(path)
    for row in rows:
        row.update({key: value for key, value in base.items() if key != "source_path"})
    return rows
