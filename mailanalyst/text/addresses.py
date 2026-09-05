from __future__ import annotations
from typing import Iterable
from email.utils import getaddresses
from mailanalyst.parsing.mime import header_value


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
