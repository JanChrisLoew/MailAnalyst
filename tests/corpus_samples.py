"""Mixed synthetic corpus: real MSG/EML inputs, separate negative file probes."""

from email.message import EmailMessage
from email.policy import SMTP
import json
import zipfile

from tests.msg_samples import CASES, write_msg


MSG_CASES = (*(case for case in CASES if case["name"] not in {"rtf", "embedded"}),
    {"name": "ansi", "ansi": True, "subject": "Ältere Nachricht – 1252", "body": "Grüße, Öl und 10 €.",
     "date": "2024-02-29T12:00:00+00:00"},
    {"name": "emoji", "subject": "Unicode 😀 日本語", "body": "Grüße 😀 日本語 العربية",
     "date": "2026-01-01T00:00:00+00:00"},
    {"name": "empty", "subject": "", "body": "", "date": ""},
    {"name": "large", "subject": "Langer Text", "body": "Synthetische Zeile.\n" * 5000, "date": ""},
    {"name": "attachments", "subject": "Mehrere Anlagen", "body": "Drei Dateinamen.", "date": "",
     "attachments": ["Prüfung.pdf", "Tabelle.xlsx", "daten.zip"]},
    {"name": "formula", "subject": "=1+1", "body": "Nur Text, keine Formel.", "date": ""},
)

EML_CASES = (
    {"name": "utf8", "subject": "Grüße 😀 日本語", "body": "Nachricht 😀 mit Umlauten."},
    {"name": "latin1", "subject": "Ältere EML", "body": "Grüße aus Köln.", "charset": "iso-8859-1"},
    {"name": "base64", "subject": "Base64", "body": "Codierter Inhalt: öäü.", "cte": "base64"},
    {"name": "quoted", "subject": "Quoted printable", "body": "Lange Zeile ö " * 40,
     "cte": "quoted-printable"},
    {"name": "html", "subject": "HTML-Mail", "body": "<p>Nur <b>HTML</b>.</p>", "html": True,
     "contains": "HTML"},
    {"name": "alternative", "subject": "Zwei Textvarianten", "body": "Klartext bevorzugen.",
     "alternative": "<p>Alternative HTML-Fassung.</p>"},
    {"name": "attachments", "subject": "Dateianlagen", "body": "Mit Anlagen.",
     "attachments": ["bericht.pdf", "tabelle.xlsx", "bild.png", "paket.zip"]},
    {"name": "empty", "subject": "Leerer Body", "body": ""},
    {"name": "undated", "subject": "Ohne Datum", "body": "Kein Datum.", "date": ""},
    {"name": "reply", "subject": "Re: Nachricht", "body": "Antwort.", "reply": True},
    {"name": "formula", "subject": "=1+1", "body": "Metadaten sind Text."},
    {"name": "large", "subject": "Große EML", "body": "Synthetischer Absatz.\n" * 5000},
)


def write_eml(path, case, message_id):
    mail = EmailMessage(policy=SMTP)
    mail["From"] = "Anna Test <anna@example.test>"
    mail["To"] = "Ben Test <ben@example.test>, Dora Test <dora@example.test>"
    mail["Cc"] = "Carla Test <carla@example.test>"
    mail["Bcc"] = "Erik Test <erik@example.test>"
    mail["Reply-To"] = "Antwort <antwort@example.test>"
    mail["Message-ID"] = message_id
    mail["Subject"] = case["subject"]
    if case.get("date", True):
        mail["Date"] = "Mon, 31 Aug 2026 23:30:00 +0000"
    if case.get("reply"):
        mail["In-Reply-To"] = "<original@example.test>"
        mail["References"] = "<original@example.test>"
    mail.set_content(case["body"], subtype="html" if case.get("html") else "plain",
                     charset=case.get("charset", "utf-8"), cte=case.get("cte", "quoted-printable"))
    if case.get("alternative"):
        mail.add_alternative(case["alternative"], subtype="html")
    for name in case.get("attachments", []):
        mail.add_attachment(b"Synthetic inventory payload, not a real document.",
                            maintype="application", subtype="octet-stream", filename=name)
    path.write_bytes(mail.as_bytes())


def create_corpus(root, repeat=1):
    """Require a new root. Return expectations keyed by relative input path."""
    if not 1 <= repeat <= 1000:
        raise ValueError("repeat must be between 1 and 1000")
    root.mkdir(parents=True, exist_ok=False)
    expected = {}
    for copy in range(repeat):
        for extension, cases in (("msg", MSG_CASES), ("eml", EML_CASES)):
            directory = root / "input" / f"batch-{copy:04d}" / extension
            directory.mkdir(parents=True)
            for spec in cases:
                case = {**spec, "name": f"{extension}-{spec['name']}-{copy}"}
                path = directory / (spec["name"] + (".MSG" if spec["name"] == "emoji" else "." + extension))
                message_id = f"<{case['name']}@example.test>"
                if extension == "msg":
                    write_msg(path, case)
                else:
                    write_eml(path, case, message_id)
                attachments = spec.get("attachments", [spec["attachment"]] if "attachment" in spec else [])
                expected[path.relative_to(root / "input").as_posix()] = {
                    "message_id": message_id, "subject": spec["subject"],
                    "body_contains": spec.get("body_contains", spec.get("contains", spec.get("body", ""))).strip(),
                    "sent_at_utc": spec.get("date", "2026-08-31T23:30:00+00:00"),
                    "attachment_names": "; ".join(attachments), "attachment_count": len(attachments),
                }
    negative = root / "negative"
    negative.mkdir()
    probes = {"empty.eml": b"", "empty.msg": b"", "broken.msg": b"not an OLE container",
              "broken.pst": b"not a PST archive", "no_headers.eml": b"not a mail",
              "notes.txt": b"Synthetic plain document", "web.html": b"<p>Synthetic document</p>"}
    for name, data in probes.items():
        (negative / name).write_bytes(data)
    with zipfile.ZipFile(negative / "archive.zip", "w") as archive:
        archive.writestr("readme.txt", "Synthetic ZIP; not an email source")
    (root / "expected.json").write_text(json.dumps(expected, ensure_ascii=False, indent=2), encoding="utf-8")
    return expected
