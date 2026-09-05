from __future__ import annotations
from pathlib import Path
from mailanalyst.text.cleaning import clean_plain_text
from mailanalyst.text.dates import derive_date_fields
from mailanalyst.text.addresses import first_address
from mailanalyst.text.addresses import format_address_emails
from mailanalyst.text.html import html_to_text
from mailanalyst.text.dates import parse_datetime


def parse_msg(path: Path, timezone_name: str) -> dict[str, object]:
    """Parst eine Outlook-MSG-Datei mit extract-msg."""
    try:
        import extract_msg
    except ImportError as exc:
        raise RuntimeError("MSG-Unterstuetzung fehlt. Bitte 'pip install -r requirements.txt' ausfuehren.") from exc

    message = extract_msg.openMsg(str(path))
    try:
        sender = str(getattr(message, "sender", "") or "")
        from_name, from_email = first_address(sender)
        raw_date = str(getattr(message, "date", "") or "")
        sent_at, sent_at_utc = parse_datetime(raw_date)
        body_text_raw = str(getattr(message, "body", "") or "")
        raw_html = getattr(message, "htmlBody", "") or ""
        body_html = raw_html.decode("utf-8", errors="replace") if isinstance(raw_html, bytes) else str(raw_html)
        body_text_clean = clean_plain_text(body_text_raw) or html_to_text(body_html)
        attachments = [str(getattr(item, "longFilename", None) or getattr(item, "shortFilename", None) or "")
                       for item in (getattr(message, "attachments", []) or [])]
        header = getattr(message, "headerDict", {}) or {}
        return {
            "message_id": str(header.get("Message-ID", header.get("Message-Id", "")) or ""),
            "in_reply_to": str(header.get("In-Reply-To", "") or ""),
            "references": str(header.get("References", "") or ""),
            "subject": str(getattr(message, "subject", "") or ""),
            "sent_at": sent_at or raw_date,
            "sent_at_utc": sent_at_utc,
            **derive_date_fields(sent_at_utc, timezone_name),
            "from_name": from_name,
            "from_email": from_email,
            "to": str(getattr(message, "to", "") or ""),
            "to_emails": format_address_emails([str(getattr(message, "to", "") or "")]),
            "cc": str(getattr(message, "cc", "") or ""),
            "cc_emails": format_address_emails([str(getattr(message, "cc", "") or "")]),
            "bcc": str(getattr(message, "bcc", "") or ""),
            "bcc_emails": format_address_emails([str(getattr(message, "bcc", "") or "")]),
            "reply_to": "",
            "reply_to_emails": "",
            "body_text": body_text_clean,
            "body_text_raw": body_text_raw,
            "body_text_clean": body_text_clean,
            "body_text_length": len(body_text_clean),
            "body_text_raw_length": len(body_text_raw),
            "body_preview": body_text_clean[:500],
            "body_html": body_html,
            "body_html_length": len(body_html),
            "has_attachments": bool(attachments),
            "attachment_count": len(attachments),
            "attachment_names": "; ".join(name for name in attachments if name),
            "mime_defects": "",
            "parse_status": "ok",
            "parse_error": "",
        }
    finally:
        message.close()
