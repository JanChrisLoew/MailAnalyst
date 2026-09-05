"""Shared defaults; changing cache policy is a separate work item."""

import logging
from pathlib import Path

SUPPORTED_EXTENSIONS = {".eml", ".msg", ".pst"}
DEFAULT_CACHE = Path(".mailanalyst_cache") / "mail_metadata.pkl"
CACHE_SCHEMA_VERSION = 6
LOGGER = logging.getLogger("mail_analyst")
