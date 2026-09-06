from __future__ import annotations
from pathlib import Path
from mailanalyst.config import CACHE_SCHEMA_VERSION
from mailanalyst.models import FileSignature
from mailanalyst.config import LOGGER
from mailanalyst.text.dates import derive_date_fields
from mailanalyst.parsing.eml import parse_eml
from mailanalyst.parsing.msg import parse_msg
from mailanalyst.parsing.pst_libpff import parse_pst_libpff
from mailanalyst.parsing.pst_outlook import parse_pst_outlook
from mailanalyst.hashing import sha256_file


def resolve_pst_backend(backend: str) -> str:
    if backend != "auto":
        return backend
    try:
        import pypff  # noqa: F401
        return "libpff"
    except ImportError:
        return "outlook"


def parse_pst(path: Path, signature: FileSignature, timezone_name: str, backend: str) -> list[dict[str, object]]:
    """Waehlt einen expliziten oder automatisch verfuegbaren PST-Importer."""
    selected = resolve_pst_backend(backend)
    LOGGER.info("PST-Backend: %s", selected)
    if selected == "libpff":
        return parse_pst_libpff(path, signature, timezone_name)
    if selected == "outlook":
        rows = parse_pst_outlook(path, signature, timezone_name)
        for row in rows:
            row["pst_backend"] = "outlook"
        return rows
    raise ValueError(f"Unbekanntes PST-Backend: {backend}")


def parse_mail_file(path: Path, signature: FileSignature, timezone_name: str, pst_backend: str = "auto") -> list[dict[str, object]]:
    """Kapselt Fehler pro Quelle, damit eine defekte Datei den Lauf nicht abbricht."""
    base = signature.__dict__.copy()
    base.update({"source_file_path": signature.source_path, "archive_path": "", "outlook_folder": "", "outlook_entry_id": ""})
    base["cache_schema_version"] = CACHE_SCHEMA_VERSION
    if not base["file_sha256"]:
        base["file_sha256"] = sha256_file(path)
    try:
        if signature.file_ext == ".eml":
            parsed = parse_eml(path, timezone_name)
        elif signature.file_ext == ".msg":
            parsed = parse_msg(path, timezone_name)
        elif signature.file_ext == ".pst":
            return parse_pst(path, signature, timezone_name, pst_backend)
        else:
            raise ValueError(f"Nicht unterstuetztes Format: {signature.file_ext}")
        return [{**base, **parsed}]
    except Exception as exc:
        return [{
            **base,
            "message_id": "",
            "in_reply_to": "",
            "references": "",
            "subject": "",
            "sent_at": "",
            "sent_at_utc": "",
            **derive_date_fields(""),
            "from_name": "",
            "from_email": "",
            "to": "",
            "to_emails": "",
            "cc": "",
            "cc_emails": "",
            "bcc": "",
            "bcc_emails": "",
            "reply_to": "",
            "reply_to_emails": "",
            "body_text": "",
            "body_text_raw": "",
            "body_text_clean": "",
            "body_text_length": 0,
            "body_text_raw_length": 0,
            "body_preview": "",
            "body_html": "",
            "body_html_length": 0,
            "has_attachments": False,
            "attachment_count": 0,
            "attachment_names": "",
            "mime_defects": "",
            "parse_status": "error",
            "parse_error": str(exc),
        }]
