from __future__ import annotations
from bs4 import BeautifulSoup
from html.parser import HTMLParser
from mailanalyst.text.cleaning import clean_plain_text
from mailanalyst.text.cleaning import normalize_text


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


def legacy_html_to_text(value: str | None) -> str:
    if not value:
        return ""
    parser = _HTMLTextExtractor()
    parser.feed(value)
    return parser.text()


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
