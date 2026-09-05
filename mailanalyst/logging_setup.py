from __future__ import annotations
from pathlib import Path
import logging
from mailanalyst.config import LOGGER


def default_log_path(output_path: Path) -> Path:
    """Legt die Standard-Logdatei neben den Masterexport."""
    return output_path.parent / "parse_log.txt"


def configure_logging(log_path: Path) -> None:
    """Schreibt Logs parallel in Konsole und Logdatei."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.setLevel(logging.INFO)
    for handler in LOGGER.handlers[:]:
        LOGGER.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    LOGGER.addHandler(file_handler)
    LOGGER.addHandler(console_handler)
