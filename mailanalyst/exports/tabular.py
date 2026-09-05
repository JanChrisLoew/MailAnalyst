from __future__ import annotations
from pathlib import Path
import pandas as pd


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


def write_csv(dataframe: pd.DataFrame, output_path: Path) -> None:
    dataframe.to_csv(output_path, index=False, encoding="utf-8-sig")


def write_excel(dataframe: pd.DataFrame, output_path: Path) -> None:
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
