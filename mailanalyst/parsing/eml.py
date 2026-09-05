from __future__ import annotations
from email.parser import BytesParser
from pathlib import Path
from email import policy
from mailanalyst.parsing.mime import attachment_names_from_eml
from mailanalyst.text.cleaning import clean_plain_text
from mailanalyst.text.dates import derive_date_fields
from mailanalyst.text.addresses import first_address
from mailanalyst.parsing.mime import first_body_part
from mailanalyst.text.addresses import format_address_emails
from mailanalyst.text.addresses import format_addresses
from mailanalyst.parsing.mime import header_value
from mailanalyst.text.html import html_to_text
from mailanalyst.text.cleaning import looks_like_html
from mailanalyst.text.dates import parse_datetime


def parse_eml(path: Path, timezone_name: str) -> dict[str, object]:
    """Parst eine einzelne .eml-Datei in eine tabellarische Zeile."""
    with path.open("rb") as file:
        message = BytesParser(policy=policy.default).parse(file)

    from_name, from_email = first_address(header_value(message, "From"))
    sent_at, sent_at_utc = parse_datetime(header_value(message, "Date"))
    body_text_raw = first_body_part(message, "plain")
    body_html = first_body_part(message, "html")
    body_text_clean = html_to_text(body_text_raw) if looks_like_html(body_text_raw) else clean_plain_text(body_text_raw)
    if not body_text_clean and body_html:
        body_text_clean = html_to_text(body_html)
    attachments = attachment_names_from_eml(message)

    defects = [defect.__class__.__name__ for defect in getattr(message, "defects", [])]

    return {
        "message_id": header_value(message, "Message-ID"),
        "in_reply_to": header_value(message, "In-Reply-To"),
        "references": header_value(message, "References"),
        "subject": header_value(message, "Subject"),
        "sent_at": sent_at,
        "sent_at_utc": sent_at_utc,
        **derive_date_fields(sent_at_utc, timezone_name),
        "from_name": from_name,
        "from_email": from_email,
        "to": format_addresses(message.get_all("To", [])),
        "to_emails": format_address_emails(message.get_all("To", [])),
        "cc": format_addresses(message.get_all("Cc", [])),
        "cc_emails": format_address_emails(message.get_all("Cc", [])),
        "bcc": format_addresses(message.get_all("Bcc", [])),
        "bcc_emails": format_address_emails(message.get_all("Bcc", [])),
        "reply_to": format_addresses(message.get_all("Reply-To", [])),
        "reply_to_emails": format_address_emails(message.get_all("Reply-To", [])),
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
        "mime_defects": "; ".join(defects),
        "parse_status": "ok",
        "parse_error": "",
    }
