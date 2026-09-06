"""Shared defaults and message schema compatibility."""

import logging
from pathlib import Path

SUPPORTED_EXTENSIONS = {".eml", ".msg", ".pst"}
DEFAULT_CACHE = Path(".mailanalyst_cache") / "mail_metadata.sqlite3"
CACHE_SCHEMA_VERSION = 6
LOGGER = logging.getLogger("mail_analyst")
