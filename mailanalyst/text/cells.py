"""Render untrusted strings as spreadsheet text without changing master data."""


import re


def csv_text(value):
    if not isinstance(value, str) or not value:
        return value
    candidate = re.sub(r"^[\s\x00-\x1f\ufeff]+", "", value)
    if value[0] in "\t\r\n" or candidate.startswith(("=", "+", "-", "@", "＝", "＋", "－", "＠")):
        return "'" + value
    return value
