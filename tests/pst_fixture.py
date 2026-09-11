"""Pinned public PST fixture metadata and expected non-personal content."""

from pathlib import Path
import hashlib

PST_FIXTURE_URL = (
    "https://raw.githubusercontent.com/libyal/testdata/"
    "refs/heads/main/pst/outlook.pst"
)
PST_FIXTURE_SHA256 = "df01707f76d0e24ab913cf1ffeffa6eaf9c1d590e02102c7ed26bb3ac51d4e24"
EXPECTED_SUBJECT = "Welcome to Microsoft Office Outlook 2003"
EXPECTED_DATE = "2007-04-29T22:27:33.593000+00:00"
EXPECTED_FOLDERS = {
    "Top of Personal Folders\\Inbox",
    "Top of Personal Folders\\Recovered_Group2",
}


def require_fixture(path: Path) -> Path:
    if not path.is_file():
        raise ValueError(f"PST-Testdatei fehlt: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != PST_FIXTURE_SHA256:
        raise ValueError(f"Unerwarteter PST-Testdatei-Hash: {digest}")
    return path.resolve()
