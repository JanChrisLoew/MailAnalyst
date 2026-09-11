# Datenvertrag und Exporthärtung – Prüfbericht

Stand: 11. September 2026

## Umfang

Der Block setzt DATA-07 und EXPORT-01 für den Entwicklungskandidaten
`0.6.0-dev.1` um. Verarbeitet wurden ausschließlich synthetische Testdaten.
Echte Mailbestände und PST-Dateien waren nicht Teil dieses Auftrags.

## Umsetzung

- Nachrichtenvertrag Version 1 prüft skalare Werte, Pflichtbezüge,
  bekannte Feldtypen, Parserstatus, Fehlertext und UTC-Zeitstempel.
- Fachlich mögliche Lücken werden nicht verworfen, sondern mit stabilen Codes,
  Feld, Erläuterung, Nachrichtenposition und Quellbezug dokumentiert.
- Manifest und `quality_warnings.jsonl` weisen Qualitätswarnungen laufbezogen aus,
  ohne die Masterfelder zu verändern.
- libpff übernimmt reine Empfängeranzeigen nicht mehr in `_emails`-Felder.
- Markdown maskiert strukturwirksame Metadaten und hält Mailtext in einem
  abgegrenzten Zitatbereich. Gültiges ergänzendes Unicode bleibt in XML erhalten;
  nur XML-1.0-unzulässige Steuerzeichen werden entfernt.
- Cache-Schemaversion 7 erzwingt den Neuimport älterer Zeilen mit der bisherigen
  libpff-Adresssemantik. App-, Nachrichten-, Parser-, Cache- und Speicherformat-
  version bleiben ausdrücklich getrennt.

## Automatisierte Prüfung und Build

Folgende Prüfungen bestanden in der vorhandenen Python-3.11.9-Umgebung:

- `python -m unittest discover -q`: 83 Tests bestanden.
- `python -m compileall -q mailanalyst tests mail_analyst.py mail_analyst_gui.py`.
- `python -m pip check`: keine defekten Abhängigkeiten.
- `git diff --check`: keine Whitespacefehler; Git meldete nur erwartete
  LF-/CRLF-Hinweise der Windows-Arbeitskopie.
- `build_exe.ps1`: PyInstaller 6.22.2, Build erfolgreich; Paket unter
  `dist/MailAnalyst`. Die Warnung über nicht installiertes `pytest` in internen
  pyarrow-Testmodulen betrifft keine Laufzeitabhängigkeit der Anwendung.

Die Tests decken Vertragsverletzungen, Warncodes und Warnbericht, Cachepfad,
Markdown-Strukturzeichen, HTML-Text, ergänzendes Unicode und XML-Steuerzeichen ab.
Der bestehende Mischbestand prüfte außerdem JSON-/Parquet-Inhalte und den
550-Nachrichten-Workflow einschließlich Cache.

Ein zusätzlicher direkter Service-Lauf mit zwei neu erzeugten EML-Dateien endete
mit `completed`, zwei Nachrichten, null Parserfehlern und null Qualitätswarnungen.
JSON und Parquet enthielten dieselben beiden Message-IDs. Beide Indexzeilen und
Markdown-Anker, sämtliche Manifest-Exporthashes, zwei Zeilen im Ergebnisindex und
der Zielcache wurden unabhängig geprüft. Der unmittelbare Wiederholungslauf
endete mit zwei verifizierten Cachetreffern und null Parserfehlern.

## Grenzen

Die native Windows-App-Steuerung war in dieser Sitzung nicht verfügbar. Der neu
gebaute Kandidat wurde deshalb nicht interaktiv bis zur Ergebnisansicht bedient.
Automatisierte Python-GUI-Tests und der Build bestanden, ersetzen diesen
Bediennachweis aber nicht. Die vollständig bediente EXE-Abnahme vom 10. September
bleibt ein historischer Nachweis für den vorherigen Kandidaten.

PST-Dateien, Outlook-COM, libpff und historische Archive wurden nicht praktisch
geprüft. Die Qualitätswarnungen beschreiben erkennbare Lücken; sie sind keine
Garantie fachlicher Vollständigkeit oder gültiger SMTP-Auflösung für Exchange.
