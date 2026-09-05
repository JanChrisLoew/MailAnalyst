from __future__ import annotations
from email.message import EmailMessage
from email.message import Message


def header_value(message: EmailMessage, name: str) -> str:
    value = message.get(name, "")
    return str(value) if value is not None else ""


def decode_part_payload(part: Message) -> str:
    """Dekodiert MIME-Parts tolerant gegen falsche oder unbekannte Zeichensaetze."""
    payload = part.get_payload(decode=True)
    if payload is None:
        raw_payload = part.get_payload()
        return raw_payload if isinstance(raw_payload, str) else ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def first_body_part(message: EmailMessage, subtype: str) -> str:
    """Liest den ersten passenden Body-Part, ohne Attachments als Text zu interpretieren."""
    body = message.get_body(preferencelist=(subtype,))
    if body is not None:
        try:
            return body.get_content()
        except Exception:
            return decode_part_payload(body)

    for part in message.walk():
        if part.get_content_maintype() == "multipart" or part.get_filename():
            continue
        if part.get_content_subtype() == subtype:
            return decode_part_payload(part)
    return ""


def attachment_names_from_eml(message: EmailMessage) -> list[str]:
    """Inventarisiert Anlagen, ohne deren Inhalte zu extrahieren."""
    names = []
    for part in message.walk():
        if part.get_content_disposition() == "attachment":
            names.append(part.get_filename() or "")
    return names
