"""Keep mail-controlled Markdown inside clearly delimited content areas."""

from html import escape
import re

_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+.!|\-])")


def inline_text(value, fallback=""):
    text = str(value or fallback).replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    return _SPECIAL.sub(r"\\\1", escape(text, quote=False))


def quoted_body(value):
    text = escape(str(value or ""), quote=False)
    return "\n".join("> " + line for line in text.splitlines()) or "> "
