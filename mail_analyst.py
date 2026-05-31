from __future__ import annotations

import argparse
import hashlib
import html
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage, Message
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd
from bs4 import BeautifulSoup


SUPPORTED_EXTENSIONS = {".eml"}
DEFAULT_CACHE = Path(".mailanalyst_cache") / "mail_metadata.pkl"
CACHE_SCHEMA_VERSION = 4


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


def parse_mail_file(path: Path, signature: FileSignature, timezone_name: str) -> dict[str, object]:
    """Kapselt Fehler pro Datei, damit ein defektes EML den Lauf nicht abbricht."""
    base = signature.__dict__.copy()
    base["cache_schema_version"] = CACHE_SCHEMA_VERSION
    if not base["file_sha256"]:
        base["file_sha256"] = sha256_file(path)
    try:
        if signature.file_ext == ".eml":
            parsed = parse_eml(path, timezone_name)
        else:
            raise ValueError(f"Nicht unterstuetztes Format: {signature.file_ext}")
        return {**base, **parsed}
    except Exception as exc:
        return {
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
        }


def discover_mail_files(input_path: Path) -> list[Path]:
    """Findet .eml-Dateien rekursiv oder akzeptiert eine einzelne .eml-Datei."""
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


def cached_row_matches(cached_row: pd.Series, signature: FileSignature, hash_check: bool) -> bool:
    """Prueft, ob eine Cache-Zeile fuer die aktuelle Datei wiederverwendet werden darf."""
    if cached_row.get("cache_schema_version") != CACHE_SCHEMA_VERSION:
        return False
    if cached_row.get("file_size") != signature.file_size:
        return False
    if cached_row.get("modified_at_ns") != signature.modified_at_ns:
        return False
    if hash_check and cached_row.get("file_sha256") != signature.file_sha256:
        return False
    return True


def parse_indexed_mail(index: int, total: int, path: Path, signature: FileSignature, timezone_name: str) -> tuple[int, dict[str, object]]:
    """Hilfsfunktion fuer paralleles Parsen mit stabiler Ergebnisreihenfolge."""
    print(f"[{index + 1}/{total}] Parse {path}")
    return index, parse_mail_file(path, signature, timezone_name)


def build_dataframe(
    input_path: Path,
    cache_path: Path,
    refresh: bool = False,
    hash_check: bool = False,
    workers: int = 1,
    timezone_name: str = "Europe/Berlin",
) -> pd.DataFrame:
    """Baut den vollstaendigen Master-DataFrame aus Cache und neu geparsten Mails."""
    paths = discover_mail_files(input_path)
    cached = load_cache(cache_path, refresh)
    cached_by_path = {
        row["source_path"]: row
        for _, row in cached.iterrows()
    } if not cached.empty and "source_path" in cached.columns else {}

    rows: list[dict[str, object] | None] = [None] * len(paths)
    parse_jobs: list[tuple[int, Path, FileSignature]] = []
    for index, path in enumerate(paths):
        signature = file_signature(path, include_hash=hash_check)
        cached_row = cached_by_path.get(signature.key)
        if cached_row is not None and cached_row_matches(cached_row, signature, hash_check):
            rows[index] = dict(cached_row)
            continue

        parse_jobs.append((index, path, signature))

    if workers <= 1 or len(parse_jobs) <= 1:
        for index, path, signature in parse_jobs:
            _, row = parse_indexed_mail(index, len(paths), path, signature, timezone_name)
            rows[index] = row
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(parse_indexed_mail, index, len(paths), path, signature, timezone_name)
                for index, path, signature in parse_jobs
            ]
            for future in as_completed(futures):
                index, row = future.result()
                rows[index] = row

    dataframe = pd.DataFrame(row for row in rows if row is not None)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_pickle(cache_path)
    return dataframe


def write_output(dataframe: pd.DataFrame, output_path: Path) -> None:
    """Schreibt den DataFrame je nach Dateiendung als CSV, Excel oder Parquet."""
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
    else:
        raise ValueError("Bitte .csv, .xlsx oder .parquet als Ausgabeendung verwenden.")


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
    parser = argparse.ArgumentParser(description="Outlook/Mailstore .eml Export in eine strukturierte Tabelle umwandeln.")
    parser.add_argument("--input", "-i", type=Path, default=Path("."), help="Datei oder Ordner mit .eml Dateien.")
    parser.add_argument("--output", "-o", type=Path, default=Path("out") / "mail_metadata.xlsx", help="Zieldatei: .xlsx, .csv oder .parquet.")
    parser.add_argument("--list-output", type=Path, help="Optionale reduzierte Review-/Microsoft-Lists-Datei: .xlsx oder .csv.")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE, help="Pfad zur DataFrame-Cachedatei.")
    parser.add_argument("--refresh", action="store_true", help="Cache ignorieren und alle Dateien neu parsen.")
    parser.add_argument("--hash-check", action="store_true", help="Auch unveraenderte Dateien per SHA-256 gegen den Cache pruefen. Sicherer, aber langsamer.")
    parser.add_argument("--workers", type=int, default=max(1, min(4, os.cpu_count() or 1)), help="Parallele Parser-Threads fuer neue/geaenderte Dateien.")
    parser.add_argument("--timezone", default="Europe/Berlin", help="Zeitzone fuer deutsche Datums-/Kalenderfelder.")
    return parser.parse_args()


def main() -> None:
    """Orchestriert Parsing, Cache, Masterexport und optionalen List-Export."""
    args = parse_args()
    dataframe = build_dataframe(args.input, args.cache, args.refresh, args.hash_check, args.workers, args.timezone)
    write_output(dataframe, args.output)
    if args.list_output:
        write_output(list_export_dataframe(dataframe), args.list_output)

    ok_count = int((dataframe["parse_status"] == "ok").sum()) if "parse_status" in dataframe else 0
    error_count = int((dataframe["parse_status"] == "error").sum()) if "parse_status" in dataframe else 0
    print(f"Fertig: {len(dataframe)} Dateien, {ok_count} erfolgreich, {error_count} Fehler.")
    print(f"Cache: {args.cache.resolve()}")
    print(f"Export: {args.output.resolve()}")
    if args.list_output:
        print(f"List-Export: {args.list_output.resolve()}")


if __name__ == "__main__":
    main()
