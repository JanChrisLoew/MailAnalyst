"""Versioned validation and stable quality warnings for message rows."""

from datetime import datetime, timedelta
import re

MESSAGE_SCHEMA_VERSION = 2

_STRING_FIELDS = {
    "source_path", "source_file_path", "archive_path", "outlook_folder",
    "outlook_entry_id", "pst_backend", "file_name", "file_ext", "modified_at",
    "file_sha256", "message_id", "in_reply_to", "references", "subject",
    "sent_at", "sent_at_utc", "sent_date_de", "sent_time_de",
    "sent_datetime_de", "sent_month_name_de", "sent_year_month",
    "sent_quarter", "sent_weekday_de", "from_name", "from_email", "to",
    "to_emails", "cc", "cc_emails", "bcc", "bcc_emails", "reply_to",
    "reply_to_emails", "body_text", "body_text_raw", "body_text_clean",
    "body_preview", "body_html", "attachment_names", "mime_defects",
    "parse_status", "parse_error",
}
_INTEGER_FIELDS = {
    "file_size", "modified_at_ns", "cache_schema_version", "sent_year",
    "sent_month", "sent_calendar_week", "sent_iso_year", "body_text_length",
    "body_text_raw_length", "body_html_length", "attachment_count",
    "embedded_attachment_count",
}
_EMAIL_FIELDS = ("from_email", "to_emails", "cc_emails", "bcc_emails", "reply_to_emails")
_DISPLAY_EMAIL_FIELDS = (("from_name", "from_email"), ("to", "to_emails"),
                         ("cc", "cc_emails"), ("bcc", "bcc_emails"),
                         ("reply_to", "reply_to_emails"))
_EMAIL = re.compile(r"^[^\s<>@;]+@[^\s<>@;]+\.[^\s<>@;]+$")


def _warning(code, field, detail):
    return {"code": code, "field": field, "detail": detail}


def _validate_types(row):
    for field in _STRING_FIELDS:
        if field in row and row[field] is not None and not isinstance(row[field], str):
            raise ValueError(f"Nachrichtenschema: {field} muss Text sein")
    for field in _INTEGER_FIELDS:
        value = row.get(field)
        if value not in (None, "") and type(value) is not int:
            raise ValueError(f"Nachrichtenschema: {field} muss eine Ganzzahl sein")
    if "has_attachments" in row and type(row["has_attachments"]) is not bool:
        raise ValueError("Nachrichtenschema: has_attachments muss boolesch sein")
    if row.get("parse_status") not in {"ok", "error"}:
        raise ValueError("Nachrichtenschema: parse_status muss ok oder error sein")
    for field in ("source_path", "source_file_path"):
        if not isinstance(row.get(field), str) or not row[field].strip():
            raise ValueError(f"Nachrichtenschema: Pflichtbezug {field} fehlt")


def _validate_utc(value):
    if not value:
        return
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Nachrichtenschema: sent_at_utc ist kein ISO-Zeitstempel") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("Nachrichtenschema: sent_at_utc muss UTC mit Offset enthalten")


def assess_message(row):
    """Reject contract violations and return non-fatal warning dictionaries."""
    if not isinstance(row, dict):
        raise ValueError("Nachrichtenschema: Datensatz muss ein Objekt sein")
    if any(value is not None and type(value) not in (str, int, float, bool) for value in row.values()):
        raise ValueError("Nachrichtenschema: nur skalare Feldwerte sind erlaubt")
    _validate_types(row)
    _validate_utc(row.get("sent_at_utc", ""))
    if row["parse_status"] == "error":
        if not row.get("parse_error"):
            raise ValueError("Nachrichtenschema: Fehlerzeile ohne parse_error")
        return []

    warnings = []
    if not row.get("sent_at_utc"):
        warnings.append(_warning("missing_sent_datetime", "sent_at_utc",
                                 "Kein normalisierter Versandzeitpunkt verfügbar."))
    for display, email in _DISPLAY_EMAIL_FIELDS:
        if row.get(display) and not row.get(email):
            warnings.append(_warning("unresolved_email", email,
                                     f"{display} enthält nur eine nicht aufgelöste Darstellung."))
    for field in _EMAIL_FIELDS:
        invalid = [item.strip() for item in str(row.get(field) or "").split(";")
                   if item.strip() and not _EMAIL.match(item.strip())]
        if invalid:
            warnings.append(_warning("non_smtp_address", field,
                                     "Mindestens ein Wert ist keine erkennbare SMTP-Adresse."))
    if not row.get("body_text_clean") and not row.get("body_html"):
        warnings.append(_warning("missing_body", "body_text_clean", "Kein Nachrichtentext verfügbar."))
    count = row.get("attachment_count", 0)
    if isinstance(count, int) and bool(count) != bool(row.get("has_attachments", False)):
        warnings.append(_warning("attachment_flag_mismatch", "has_attachments",
                                 "Anlagenzähler und Anlagenkennzeichen widersprechen sich."))
    if row.get("embedded_attachment_count", 0):
        warnings.append(_warning(
            "embedded_message_not_extracted", "embedded_attachment_count",
            "Eingebettete Nachricht inventarisiert; ihr innerer Inhalt wurde nicht exportiert.",
        ))
    return warnings
