from __future__ import annotations

import argparse
import hashlib
import html
import logging
import os
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage, Message
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd
from bs4 import BeautifulSoup


SUPPORTED_EXTENSIONS = {".eml", ".msg", ".pst"}
DEFAULT_CACHE = Path(".mailanalyst_cache") / "mail_metadata.pkl"
CACHE_SCHEMA_VERSION = 6
LOGGER = logging.getLogger("mail_analyst")


# Minimaler Fallback, falls BeautifulSoup bei sehr kaputtem HTML keinen Text liefert.
class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self._chunks.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"br", "p", "div", "tr", "li"}:
            self._chunks.append("\n")

    def text(self) -> str:
        return normalize_text(" ".join(self._chunks))


@dataclass(frozen=True)
class FileSignature:
    source_path: str
    file_name: str
    file_ext: str
    file_size: int
    modified_at: str
    modified_at_ns: int
    file_sha256: str

    @property
    def key(self) -> str:
        return self.source_path


def header_value(message: EmailMessage, name: str) -> str:
    value = message.get(name, "")
    return str(value) if value is not None else ""


def normalize_text(value: str | None) -> str:
    """Vereinheitlicht Whitespace, Zeilenumbrueche und HTML-Entities."""
    if not value:
        return ""
    value = html.unescape(value)
    value = value.replace("\u00a0", " ")
    value = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t\f\v]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def legacy_html_to_text(value: str | None) -> str:
    if not value:
        return ""
    parser = _HTMLTextExtractor()
    parser.feed(value)
    return parser.text()


def clean_plain_text(value: str | None) -> str:
    """Bereinigt extrahierten Mailtext fuer Suche und Review."""
    text = normalize_text(value)
    if not text:
        return ""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = text.replace("<!--", "").replace("-->", "")

    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        stripped = re.sub(r"^[>|]\s?", "", stripped)
        stripped = re.sub(r"^-{2,}$", "-" * 20, stripped)
        lines.append(stripped)
    text = "\n".join(lines)

    # Preserve Outlook reply separators but make the surrounding text easier to scan.
    text = re.sub(r"\n?Von:\s", "\n\nVon: ", text, flags=re.IGNORECASE)
    text = re.sub(r"\n?Gesendet:\s", "\nGesendet: ", text, flags=re.IGNORECASE)
    text = re.sub(r"\n?An:\s", "\nAn: ", text, flags=re.IGNORECASE)
    text = re.sub(r"\n?Cc:\s", "\nCc: ", text, flags=re.IGNORECASE)
    text = re.sub(r"\n?Betreff:\s", "\nBetreff: ", text, flags=re.IGNORECASE)
    return normalize_text(text)


def looks_like_html(value: str | None) -> bool:
    """Erkennt Plaintext-Teile, die faktisch HTML-Markup enthalten."""
    if not value:
        return False
    sample = value[:5000].lower()
    if "<html" in sample or "<body" in sample or "<!doctype" in sample:
        return True
    return len(re.findall(r"</?(?:div|p|br|table|tr|td|span|a|ul|ol|li|strong|font)\b", sample)) >= 3


def html_to_text(value: str | None) -> str:
    """Wandelt HTML-Mails in moeglichst lesbaren Plaintext um."""
    if not value:
        return ""

    soup = BeautifulSoup(value, "html.parser")
    # Technische HTML-Bloecke sind fuer die fachliche Auswertung nicht relevant.
    for element in soup(["script", "style", "meta", "head", "title", "noscript"]):
        element.decompose()

    for br in soup.find_all("br"):
        br.replace_with("\n")

    for link in soup.find_all("a"):
        text = normalize_text(link.get_text(" ", strip=True))
        href = normalize_text(link.get("href"))
        # Linkziel erhalten, damit Nachweise und Verweise spaeter nachvollziehbar bleiben.
        if href and text and href != text and not href.lower().startswith(("mailto:", "tel:")):
            link.replace_with(f"{text} ({href})")
        elif text:
            link.replace_with(text)
        elif href:
            link.replace_with(href)

    for item in soup.find_all("li"):
        item.insert_before("\n- ")
        item.append("\n")

    for row in soup.find_all("tr"):
        cells = [clean_plain_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
        if cells:
            # Tabellen nicht perfekt rekonstruieren, aber als lesbare Zeilen erhalten.
            row.replace_with("\n" + " | ".join(cell for cell in cells if cell) + "\n")

    block_tags = {
        "address",
        "article",
        "aside",
        "blockquote",
        "div",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "p",
        "pre",
        "section",
    }
    for element in soup.find_all(block_tags):
        element.insert_before("\n")
        element.append("\n")

    text = soup.get_text("\n")
    return clean_plain_text(text) or legacy_html_to_text(value)


def prepare_analysis_text(value: str | None, link_mode: str = "full") -> str:
    """Reduziert URL-Rauschen fuer Markdown, ohne die Masterdaten zu veraendern."""
    text = value or ""
    if link_mode == "full":
        return text

    url_pattern = re.compile(r"https?://[^\s\]\)>]+", re.IGNORECASE)
    media_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")
    tracking_keys = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid", "mc_cid", "mc_eid"}

    def replace(match: re.Match[str]) -> str:
        url = match.group(0)
        if link_mode == "text_only":
            return ""
        try:
            parts = urlsplit(url)
            path_lower = parts.path.lower()
            if path_lower.endswith(media_extensions):
                return ""
            query = [(key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True)
                     if key.lower() not in tracking_keys and not key.lower().startswith("utm_")]
            compact = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))
            return compact.rstrip("?")
        except ValueError:
            return ""

    text = url_pattern.sub(replace, text)
    text = re.sub(r"\[\s*\]", "", text)
    text = re.sub(r"\(\s*\)", "", text)
    return normalize_text(text)


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


def format_addresses(header_values: Iterable[str | None]) -> str:
    """Formatiert Adress-Header menschenlesbar mit Name und E-Mail."""
    addresses = getaddresses([value for value in header_values if value])
    rendered = []
    for name, address in addresses:
        if name and address:
            rendered.append(f"{name} <{address}>")
        else:
            rendered.append(address or name)
    return "; ".join(item for item in rendered if item)


def format_address_emails(header_values: Iterable[str | None]) -> str:
    """Extrahiert nur die E-Mail-Adressen fuer Filter und Listenansichten."""
    addresses = getaddresses([value for value in header_values if value])
    return "; ".join(address for _, address in addresses if address)


def first_address(header_value: str | None) -> tuple[str, str]:
    addresses = getaddresses([header_value] if header_value else [])
    if not addresses:
        return "", ""
    name, address = addresses[0]
    return name, address


def parse_datetime(value: str | None) -> tuple[str, str]:
    """Parst Mail-Datumswerte und normalisiert sie zusaetzlich auf UTC."""
    if not value:
        return "", ""
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError, OverflowError):
        return value, ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat(), parsed.astimezone(timezone.utc).isoformat()


def derive_date_fields(sent_at_utc: str, timezone_name: str = "Europe/Berlin") -> dict[str, object]:
    """Erzeugt deutsche Datumsfelder fuer Power BI, Excel und Microsoft Lists."""
    if not sent_at_utc:
        return {
            "sent_date_de": "",
            "sent_time_de": "",
            "sent_datetime_de": "",
            "sent_year": "",
            "sent_month": "",
            "sent_month_name_de": "",
            "sent_year_month": "",
            "sent_quarter": "",
            "sent_calendar_week": "",
            "sent_iso_year": "",
            "sent_weekday_de": "",
        }

    try:
        sent = datetime.fromisoformat(sent_at_utc)
        target_timezone = ZoneInfo(timezone_name)
    except (ValueError, ZoneInfoNotFoundError):
        return derive_date_fields("")

    local = sent.astimezone(target_timezone)
    iso_calendar = local.isocalendar()
    month_names = [
        "",
        "Januar",
        "Februar",
        "Maerz",
        "April",
        "Mai",
        "Juni",
        "Juli",
        "August",
        "September",
        "Oktober",
        "November",
        "Dezember",
    ]
    weekday_names = [
        "Montag",
        "Dienstag",
        "Mittwoch",
        "Donnerstag",
        "Freitag",
        "Samstag",
        "Sonntag",
    ]

    return {
        "sent_date_de": local.strftime("%d.%m.%Y"),
        "sent_time_de": local.strftime("%H:%M:%S"),
        "sent_datetime_de": local.strftime("%d.%m.%Y %H:%M:%S"),
        "sent_year": local.year,
        "sent_month": local.month,
        "sent_month_name_de": month_names[local.month],
        "sent_year_month": local.strftime("%Y-%m"),
        "sent_quarter": f"Q{((local.month - 1) // 3) + 1}",
        "sent_calendar_week": iso_calendar.week,
        "sent_iso_year": iso_calendar.year,
        "sent_weekday_de": weekday_names[local.weekday()],
    }


def attachment_names_from_eml(message: EmailMessage) -> list[str]:
    """Inventarisiert Anlagen, ohne deren Inhalte zu extrahieren."""
    names = []
    for part in message.walk():
        if part.get_content_disposition() == "attachment":
            names.append(part.get_filename() or "")
    return names


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Berechnet einen Datei-Hash fuer Nachvollziehbarkeit und optionale Cache-Pruefung."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_signature(path: Path, include_hash: bool = False) -> FileSignature:
    """Erfasst stabile Dateimerkmale fuer Cache und Nachweisfuehrung."""
    stat = path.stat()
    return FileSignature(
        source_path=str(path.resolve()),
        file_name=path.name,
        file_ext=path.suffix.lower(),
        file_size=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        modified_at_ns=stat.st_mtime_ns,
        file_sha256=sha256_file(path) if include_hash else "",
    )


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


def parse_pst(path: Path, signature: FileSignature, timezone_name: str, backend: str) -> list[dict[str, object]]:
    """Waehlt einen expliziten oder automatisch verfuegbaren PST-Importer."""
    selected = backend
    if selected == "auto":
        try:
            import pypff  # noqa: F401
            selected = "libpff"
        except ImportError:
            selected = "outlook"
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


def discover_mail_files(input_path: Path) -> list[Path]:
    """Findet unterstuetzte Maildateien rekursiv oder akzeptiert eine einzelne Datei."""
    if input_path.is_file():
        return [input_path] if input_path.suffix.lower() in SUPPORTED_EXTENSIONS else []
    return sorted(
        path
        for path in input_path.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def load_cache(cache_path: Path, refresh: bool) -> pd.DataFrame:
    """Laedt den DataFrame-Cache, sofern kein kompletter Neuaufbau angefordert ist."""
    if refresh or not cache_path.exists():
        return pd.DataFrame()
    return pd.read_pickle(cache_path)


def cached_row_matches(cached_row: pd.Series, signature: FileSignature, hash_check: bool, pst_backend: str) -> bool:
    """Prueft, ob eine Cache-Zeile fuer die aktuelle Datei wiederverwendet werden darf."""
    if cached_row.get("cache_schema_version") != CACHE_SCHEMA_VERSION:
        return False
    if cached_row.get("file_size") != signature.file_size:
        return False
    if cached_row.get("modified_at_ns") != signature.modified_at_ns:
        return False
    if hash_check and cached_row.get("file_sha256") != signature.file_sha256:
        return False
    if signature.file_ext == ".pst" and pst_backend != "auto" and cached_row.get("pst_backend") != pst_backend:
        return False
    return True


def parse_indexed_mail(index: int, total: int, path: Path, signature: FileSignature, timezone_name: str, pst_backend: str) -> tuple[int, list[dict[str, object]]]:
    """Hilfsfunktion fuer paralleles Parsen mit stabiler Ergebnisreihenfolge."""
    LOGGER.info("[%s/%s] Parse %s", index + 1, total, path)
    return index, parse_mail_file(path, signature, timezone_name, pst_backend)


def build_dataframe(
    input_path: Path,
    cache_path: Path,
    refresh: bool = False,
    hash_check: bool = False,
    workers: int = 1,
    timezone_name: str = "Europe/Berlin",
    pst_backend: str = "auto",
    paths_override: list[Path] | None = None,
    progress_callback: Callable[[int, int, Path, str], None] | None = None,
) -> pd.DataFrame:
    """Baut den vollstaendigen Master-DataFrame aus Cache und neu geparsten Mails."""
    paths = paths_override if paths_override is not None else discover_mail_files(input_path)
    if any(path.suffix.lower() == ".pst" for path in paths):
        workers = 1  # Outlook-COM und PST-Stores werden bewusst seriell verarbeitet.
    cached = load_cache(cache_path, refresh)
    cached_by_path: dict[str, list[dict[str, object]]] = {}
    if not cached.empty and "source_path" in cached.columns:
        for _, row in cached.iterrows():
            key = str(row.get("source_file_path") or row.get("source_path"))
            cached_by_path.setdefault(key, []).append(dict(row))

    rows: list[list[dict[str, object]] | None] = [None] * len(paths)
    parse_jobs: list[tuple[int, Path, FileSignature]] = []
    for index, path in enumerate(paths):
        signature = file_signature(path, include_hash=hash_check)
        cached_rows = cached_by_path.get(signature.key)
        if cached_rows and cached_row_matches(pd.Series(cached_rows[0]), signature, hash_check, pst_backend):
            rows[index] = cached_rows
            if progress_callback:
                progress_callback(index + 1, len(paths), path, "cache")
            continue

        parse_jobs.append((index, path, signature))

    if workers <= 1 or len(parse_jobs) <= 1:
        for index, path, signature in parse_jobs:
            _, row = parse_indexed_mail(index, len(paths), path, signature, timezone_name, pst_backend)
            rows[index] = row
            if progress_callback:
                progress_callback(index + 1, len(paths), path, "parsed")
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(parse_indexed_mail, index, len(paths), path, signature, timezone_name, pst_backend)
                for index, path, signature in parse_jobs
            ]
            for future in as_completed(futures):
                index, row = future.result()
                rows[index] = row
                if progress_callback:
                    completed = sum(item is not None for item in rows)
                    progress_callback(completed, len(paths), paths[index], "parsed")

    dataframe = pd.DataFrame(row for source_rows in rows if source_rows is not None for row in source_rows)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_pickle(cache_path)
    return dataframe


def write_output(dataframe: pd.DataFrame, output_path: Path, markdown_link_mode: str = "full") -> None:
    """Schreibt den DataFrame als Tabelle oder gut lesbares Austauschdokument."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()
    if suffix == ".csv":
        dataframe.to_csv(output_path, index=False, encoding="utf-8-sig")
    elif suffix in {".xlsx", ".xlsm"}:
        dataframe = dataframe.copy()
        excel_limit = 32767
        # Excel kann pro Zelle maximal 32.767 Zeichen speichern.
        for column in dataframe.columns:
            if not dataframe[column].map(lambda value: isinstance(value, str)).any():
                continue
            dataframe[column] = dataframe[column].map(
                lambda value: value[:excel_limit] if isinstance(value, str) and len(value) > excel_limit else value
            )
        dataframe.to_excel(output_path, index=False)
    elif suffix == ".parquet":
        dataframe.to_parquet(output_path, index=False)
    elif suffix == ".json":
        dataframe.to_json(output_path, orient="records", force_ascii=False, indent=2, date_format="iso")
    elif suffix == ".xml":
        root = ET.Element("emails", count=str(len(dataframe)))
        for _, row in dataframe.iterrows():
            email_node = ET.SubElement(root, "email")
            for column, value in row.items():
                node = ET.SubElement(email_node, str(column))
                if not pd.isna(value):
                    node.text = re.sub(r"[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]", "", str(value))
        ET.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)
    elif suffix in {".md", ".markdown"}:
        with output_path.open("w", encoding="utf-8", newline="\n") as file:
            file.write(f"# MailAnalyst Export\n\n{len(dataframe)} Nachrichten\n\n")
            for number, (_, row) in enumerate(dataframe.iterrows(), start=1):
                subject = str(row.get("subject", "") or "(ohne Betreff)").replace("\n", " ")
                file.write(f"## {number}. {subject}\n\n")
                for label, column in (("Datum", "sent_datetime_de"), ("Von", "from_email"),
                                      ("An", "to_emails"), ("CC", "cc_emails"),
                                      ("Anlagen", "attachment_names"), ("Quelle", "source_path")):
                    value = str(row.get(column, "") or "").replace("\n", " ")
                    if value:
                        file.write(f"- **{label}:** {value}\n")
                file.write("\n### Inhalt\n\n")
                body = prepare_analysis_text(str(row.get("body_text_clean", "") or ""), markdown_link_mode)
                file.write(body.replace("\n#", "\n\\#") + "\n\n---\n\n")
    else:
        raise ValueError("Bitte .csv, .xlsx, .parquet, .json, .xml oder .md als Ausgabeendung verwenden.")


def write_markdown_dataset(dataframe: pd.DataFrame, output_dir: Path, link_mode: str = "full") -> None:
    """Schreibt chronologische Monatsdateien plus maschinenlesbaren Suchindex."""
    output_dir.mkdir(parents=True, exist_ok=True)
    data = dataframe.copy()
    if "sent_at_utc" in data.columns:
        parsed_dates = pd.to_datetime(data["sent_at_utc"], errors="coerce", utc=True)
    else:
        parsed_dates = pd.Series(pd.NaT, index=data.index, dtype="datetime64[ns, UTC]")
    data["_chunk"] = parsed_dates.dt.strftime("%Y-%m").fillna("unbekannt")
    data["_sort_date"] = parsed_dates
    data = data.sort_values(["_sort_date", "subject"], na_position="last")

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
                subject = str(row.get("subject", "") or "(ohne Betreff)").replace("\n", " ")
                file.write(f"<a id=\"{anchor}\"></a>\n\n## {number}. {subject}\n\n")
                metadata = (
                    ("Datum", "sent_datetime_de"), ("Von", "from_email"), ("An", "to_emails"),
                    ("CC", "cc_emails"), ("Message-ID", "message_id"), ("Anlagen", "attachment_names"),
                    ("PST-Ordner", "outlook_folder"), ("Quelle", "source_path"),
                )
                for label, column in metadata:
                    value = str(row.get(column, "") or "").replace("\n", " ")
                    if value and value.lower() != "nan":
                        file.write(f"- **{label}:** {value}\n")
                file.write("\n### Inhalt\n\n")
                body = prepare_analysis_text(str(row.get("body_text_clean", "") or ""), link_mode)
                file.write(body.replace("\n#", "\n\\#") + "\n\n---\n\n")
                index_rows.append({
                    "chunk": chunk,
                    "markdown_file": str(chunk_path.relative_to(output_dir)),
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
    index_frame.to_csv(output_dir / "index.csv", index=False, encoding="utf-8-sig")


def default_log_path(output_path: Path) -> Path:
    """Legt die Standard-Logdatei neben den Masterexport."""
    return output_path.parent / "parse_log.txt"


def configure_logging(log_path: Path) -> None:
    """Schreibt Logs parallel in Konsole und Logdatei."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.setLevel(logging.INFO)
    LOGGER.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    LOGGER.addHandler(file_handler)
    LOGGER.addHandler(console_handler)


def list_export_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Reduziert den Masterdatensatz auf eine menschenlesbare Review-/Listenansicht."""
    columns = [
        "sent_datetime_de",
        "sent_date_de",
        "sent_time_de",
        "sent_year",
        "sent_month",
        "sent_month_name_de",
        "sent_year_month",
        "sent_quarter",
        "sent_calendar_week",
        "sent_iso_year",
        "sent_weekday_de",
        "from_name",
        "from_email",
        "to_emails",
        "cc_emails",
        "subject",
        "body_preview",
        "has_attachments",
        "attachment_count",
        "attachment_names",
        "source_path",
        "message_id",
        "parse_status",
        "parse_error",
    ]
    available_columns = [column for column in columns if column in dataframe.columns]
    return dataframe.loc[:, available_columns].rename(
        columns={
            "sent_datetime_de": "Gesendet am",
            "sent_date_de": "Datum",
            "sent_time_de": "Uhrzeit",
            "sent_year": "Jahr",
            "sent_month": "Monat",
            "sent_month_name_de": "Monatsname",
            "sent_year_month": "Jahr-Monat",
            "sent_quarter": "Quartal",
            "sent_calendar_week": "Kalenderwoche",
            "sent_iso_year": "ISO-Jahr",
            "sent_weekday_de": "Wochentag",
            "from_name": "Absender Name",
            "from_email": "Absender E-Mail",
            "to_emails": "Empfaenger",
            "cc_emails": "CC",
            "subject": "Betreff",
            "body_preview": "Textauszug",
            "has_attachments": "Hat Anlagen",
            "attachment_count": "Anzahl Anlagen",
            "attachment_names": "Anlagen",
            "source_path": "Quelldatei",
            "message_id": "Message-ID",
            "parse_status": "Parser Status",
            "parse_error": "Parser Fehler",
        }
    )


def parse_args() -> argparse.Namespace:
    """Definiert die Kommandozeilenoptionen fuer den Batchlauf."""
    parser = argparse.ArgumentParser(description="Outlook-Dateien (.eml, .msg, .pst) strukturiert exportieren.")
    parser.add_argument("--input", "-i", type=Path, default=Path("."), help="Datei oder Ordner mit .eml, .msg oder .pst Dateien.")
    parser.add_argument("--output", "-o", type=Path, default=Path("out") / "mail_metadata.xlsx", help="Zieldatei: .xlsx, .csv, .parquet, .json, .xml oder .md.")
    parser.add_argument("--list-output", type=Path, help="Optionale reduzierte Review-/Microsoft-Lists-Datei: .xlsx oder .csv.")
    parser.add_argument("--markdown-dir", type=Path,
                        help="Optionaler Markdown-Datensatz: Monatsdateien nach Jahren plus index.csv/index.jsonl.")
    parser.add_argument("--log-output", type=Path, help="Optionale Logdatei. Standard: parse_log.txt neben dem Masterexport.")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE, help="Pfad zur DataFrame-Cachedatei.")
    parser.add_argument("--refresh", action="store_true", help="Cache ignorieren und alle Dateien neu parsen.")
    parser.add_argument("--hash-check", action="store_true", help="Auch unveraenderte Dateien per SHA-256 gegen den Cache pruefen. Sicherer, aber langsamer.")
    parser.add_argument("--workers", type=int, default=max(1, min(4, os.cpu_count() or 1)), help="Parallele Parser-Threads fuer neue/geaenderte Dateien.")
    parser.add_argument("--timezone", default="Europe/Berlin", help="Zeitzone fuer deutsche Datums-/Kalenderfelder.")
    parser.add_argument("--pst-backend", choices=("auto", "libpff", "outlook"), default="auto",
                        help="PST-Importer: automatisch, Outlook-unabhaengiges libpff oder klassisches Outlook.")
    return parser.parse_args()


def main() -> None:
    """Orchestriert Parsing, Cache, Masterexport und optionalen List-Export."""
    args = parse_args()
    log_path = args.log_output or default_log_path(args.output)
    configure_logging(log_path)

    started_at = datetime.now(timezone.utc)
    LOGGER.info("Start MailAnalyst")
    LOGGER.info("Input: %s", args.input.resolve())
    LOGGER.info("Output: %s", args.output.resolve())
    if args.list_output:
        LOGGER.info("List-Output: %s", args.list_output.resolve())
    if args.markdown_dir:
        LOGGER.info("Markdown-Ordner: %s", args.markdown_dir.resolve())
    LOGGER.info("Cache: %s", args.cache.resolve())
    LOGGER.info("Timezone: %s", args.timezone)
    LOGGER.info("Refresh: %s", args.refresh)
    LOGGER.info("Hash-Check: %s", args.hash_check)
    LOGGER.info("Workers: %s", args.workers)

    dataframe = build_dataframe(args.input, args.cache, args.refresh, args.hash_check, args.workers, args.timezone, args.pst_backend)
    write_output(dataframe, args.output)
    if args.list_output:
        write_output(list_export_dataframe(dataframe), args.list_output)
    if args.markdown_dir:
        write_markdown_dataset(dataframe, args.markdown_dir)

    ok_count = int((dataframe["parse_status"] == "ok").sum()) if "parse_status" in dataframe else 0
    error_count = int((dataframe["parse_status"] == "error").sum()) if "parse_status" in dataframe else 0
    elapsed_seconds = (datetime.now(timezone.utc) - started_at).total_seconds()
    LOGGER.info("Fertig: %s Dateien, %s erfolgreich, %s Fehler.", len(dataframe), ok_count, error_count)
    if error_count and {"source_path", "parse_error"}.issubset(dataframe.columns):
        for _, row in dataframe[dataframe["parse_status"] == "error"].iterrows():
            LOGGER.error("Parse-Fehler: %s | %s", row.get("source_path", ""), row.get("parse_error", ""))
    LOGGER.info("Laufzeit Sekunden: %.2f", elapsed_seconds)
    LOGGER.info("Cache: %s", args.cache.resolve())
    LOGGER.info("Export: %s", args.output.resolve())
    if args.list_output:
        LOGGER.info("List-Export: %s", args.list_output.resolve())
    if args.markdown_dir:
        LOGGER.info("Markdown-Ordner: %s", args.markdown_dir.resolve())
    LOGGER.info("Log: %s", log_path.resolve())


if __name__ == "__main__":
    main()
