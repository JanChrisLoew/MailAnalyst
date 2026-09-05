from __future__ import annotations
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError
from datetime import datetime
from email.utils import parsedate_to_datetime
from datetime import timezone


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
