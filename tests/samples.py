"""Synthetic messages only; no project mailbox data is used in tests."""

import os
from email.message import EmailMessage
from pathlib import Path


def create_sources(root: Path) -> Path:
    source = root / "input"
    source.mkdir()
    for name, date, subject in (
        ("first", "Mon, 31 Aug 2026 23:30:00 +0000", "Freigabe Bauabschnitt"),
        ("second", "Tue, 01 Sep 2026 12:00:00 +0200", "Re: Freigabe Bauabschnitt"),
    ):
        message = EmailMessage()
        message["From"] = "Projektleitung <leitung@example.test>"
        message["To"] = "Bauleitung <bau@example.test>"
        message["Cc"] = "Pruefung <pruefung@example.test>"
        message["Subject"] = subject
        message["Date"] = date
        message["Message-ID"] = f"<{name}@example.test>"
        if name == "first":
            message.set_content("Freigabe erfolgt.\nBitte Termin bestaetigen.")
            message.add_attachment(b"synthetic attachment", maintype="application",
                                   subtype="octet-stream", filename="beleg.txt")
            message.set_boundary("mailanalyst-test-boundary")
        else:
            message["In-Reply-To"] = "<first@example.test>"
            message.set_content(
                '<html><body><p>Termin bestaetigt.</p><a href="https://example.test/plan?utm_source=mail&id=7">Plan</a></body></html>',
                subtype="html",
            )
        path = source / f"{name}.eml"
        path.write_bytes(message.as_bytes())
        os.utime(path, ns=(1700000000000000000, 1700000000000000000))
    (source / "ignored.txt").write_text("not a mail", encoding="utf-8")
    return source


def portable_frame(frame):
    frame = frame.copy()
    for column in ("source_path", "source_file_path"):
        if column in frame:
            frame[column] = frame[column].map(lambda value: "SOURCE/" + Path(value).name)
    return frame
