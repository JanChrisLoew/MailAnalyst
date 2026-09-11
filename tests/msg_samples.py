"""Generate small Unicode MSG containers with invented, independently specified data.

Uses extract-msg's CFB writer only, never MailAnalyst parsing/normalization.
Property layout follows MS-OXMSG; files are generated outside version control.
"""

from datetime import datetime, timezone
import struct

import compressed_rtf
from extract_msg.ole_writer import OleWriter


CASES = (
    {"name": "plain", "subject": "Prüfung – Grüße", "body": "Grüße aus dem synthetischen Archiv.",
     "date": "2026-08-31T23:30:00+00:00", "local": "01.09.2026 01:30:00"},
    {"name": "html", "subject": "HTML und Anlage", "html": "<p>Freigabe <b>bestätigt</b>.</p>",
     "body_contains": "bestätigt", "attachment": "beleg.txt",
     "date": "2026-10-25T01:30:00+00:00", "local": "25.10.2026 02:30:00"},
    {"name": "reply", "subject": "Re: Prüfung – Grüße", "body": "Antwort mit Bezug.",
     "reply": "<plain@example.test>", "date": "2026-03-29T01:30:00+00:00",
     "local": "29.03.2026 03:30:00"},
    {"name": "rtf", "subject": "Nur RTF",
     "rtf": (r"{\rtf1\ansi\ansicpg1252\fromtext\deff0{\fonttbl{\f0\fnil Arial;}}"
             r"\viewkind4\uc1\pard\f0\fs20 RTF-Inhalt mit Umlaut: Gr\'fc\'dfe.\par}"),
     "body_contains": "RTF-Inhalt mit Umlaut: Grüße.",
     "date": "2026-06-15T10:00:00+00:00", "local": "15.06.2026 12:00:00"},
    {"name": "embedded", "subject": "Weitergeleitete Nachricht", "body": "Siehe Anlage.",
     "embedded_attachment": "ursprung.msg", "embedded_subject": "Innerer Prüfbetreff",
     "date": "2026-07-20T08:15:00+00:00", "local": "20.07.2026 10:15:00"},
    {"name": "undated", "subject": "Ohne Versanddatum", "body": "Kein Datum vorhanden.",
     "date": "", "local": ""},
)


def write_msg(path, case):
    writer = OleWriter()
    ansi = case.get("ansi", False)
    for stream in ("00020102", "00030102", "00040102"):
        writer.addEntry("__nameid_version1.0/__substg1.0_" + stream, b"")

    def properties(prefix, strings, numbers=(), binaries=(), header=b"\0" * 8):
        entries = []
        for tag, value in strings.items():
            kind = 0x1E if ansi else 0x1F
            data = value.encode("cp1252" if ansi else "utf-16-le")
            writer.addEntry(prefix + f"__substg1.0_{tag:04X}{kind:04X}", data)
            entries.append(struct.pack("<IIII", tag << 16 | kind, 6, len(data) + (1 if ansi else 2), 0))
        for tag, kind, value in numbers:
            entries.append(struct.pack("<IIQ", tag << 16 | kind, 6, value))
        for tag, data in binaries:
            writer.addEntry(prefix + f"__substg1.0_{tag:04X}0102", data)
            entries.append(struct.pack("<IIII", tag << 16 | 0x102, 6, len(data), 0))
        writer.addEntry(prefix + "__properties_version1.0", header + b"".join(entries))

    message_id = f"<{case['name']}@example.test>"
    headers = (f"From: Anna Test <anna@example.test>\r\nTo: Ben Test <ben@example.test>\r\n"
               f"Cc: Carla Test <carla@example.test>\r\nMessage-ID: {message_id}\r\n")
    if case.get("reply"):
        headers += f"In-Reply-To: {case['reply']}\r\nReferences: {case['reply']}\r\n"
    strings = {0x001A: "IPM.Note", 0x0037: case["subject"], 0x007D: headers,
               0x0C1A: "Anna Test", 0x0C1E: "SMTP", 0x0C1F: "anna@example.test",
               0x5D01: "anna@example.test", 0x1035: message_id,
               0x0E04: "Ben Test", 0x0E03: "Carla Test"}
    if "body" in case:
        strings[0x1000] = case["body"]
    attachments = case.get("attachments", [case["attachment"]] if "attachment" in case else [])
    attachment_count = len(attachments) + int("embedded_attachment" in case)
    numbers = [(0x340D, 3, 0 if ansi else 0x40000), (0x0E07, 3, 1),
               (0x3FFD, 3, 1252 if ansi else 65001), (0x3FDE, 3, 65001)]
    if case["date"]:
        date = datetime.fromisoformat(case["date"])
        epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
        numbers.append((0x0039, 0x40, int((date - epoch).total_seconds()) * 10_000_000))
    binaries = [(0x1013, case["html"].encode("utf-8"))] if "html" in case else []
    if "rtf" in case:
        binaries.append((0x1009, compressed_rtf.compress(case["rtf"].encode("ascii"))))
    header = struct.pack("<8sIIII8s", b"", 2, attachment_count, 2, attachment_count, b"")
    properties("", strings, numbers, binaries, header)
    for index, (name, address) in enumerate((("Ben Test", "ben@example.test"),
                                           ("Carla Test", "carla@example.test"))):
        properties(f"__recip_version1.0_#{index:08X}/",
                   {0x3001: name, 0x3002: "SMTP", 0x3003: address, 0x39FE: address},
                   [(0x0C15, 3, index + 1), (0x3000, 3, index)])
    for index, name in enumerate(attachments):
        properties(f"__attach_version1.0_#{index:08X}/",
                   {0x3704: name, 0x3707: name, 0x370E: "application/octet-stream"},
                   [(0x3705, 3, 1), (0x0E21, 3, index), (0x0E20, 3, 20)],
                   [(0x3701, b"Synthetic attachment")])
    if "embedded_attachment" in case:
        index = len(attachments)
        name = case["embedded_attachment"]
        prefix = f"__attach_version1.0_#{index:08X}/"
        properties(prefix, {0x3704: name, 0x3707: name, 0x370E: "application/vnd.ms-outlook"},
                   [(0x3705, 3, 5), (0x0E21, 3, index), (0x0E20, 3, 20)])
        embedded = prefix + "__substg1.0_3701000D/"
        embedded_id = "<embedded-inner@example.test>"
        embedded_headers = (f"From: Innere Quelle <inner@example.test>\r\n"
                            f"Message-ID: {embedded_id}\r\n")
        embedded_strings = {
            0x001A: "IPM.Note", 0x0037: case["embedded_subject"],
            0x007D: embedded_headers, 0x0C1A: "Innere Quelle",
            0x0C1E: "SMTP", 0x0C1F: "inner@example.test",
            0x1000: "Inhalt der eingebetteten synthetischen Nachricht.",
            0x1035: embedded_id,
        }
        embedded_numbers = [(0x340D, 3, 0x40000), (0x0E07, 3, 1),
                            (0x3FFD, 3, 65001), (0x3FDE, 3, 65001)]
        embedded_header = struct.pack("<8sIIII", b"", 0, 0, 0, 0)
        properties(embedded, embedded_strings, embedded_numbers, header=embedded_header)
    writer.write(path)


def create_msg_sources(root):
    source = root / "input"
    source.mkdir(parents=True)
    for case in CASES:
        write_msg(source / (case["name"] + ".msg"), case)
    return source
