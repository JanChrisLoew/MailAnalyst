from __future__ import annotations
from urllib.parse import parse_qsl
import re
from urllib.parse import urlencode
from urllib.parse import urlsplit
from urllib.parse import urlunsplit
from mailanalyst.text.cleaning import normalize_text


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
