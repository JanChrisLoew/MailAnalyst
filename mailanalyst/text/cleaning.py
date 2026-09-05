from __future__ import annotations
import html
import re


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
