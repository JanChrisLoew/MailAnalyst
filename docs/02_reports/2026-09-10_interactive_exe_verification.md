# Interaktive EXE-Prüfung von 0.5.0-dev.1

Stand: 10. September 2026. Nach ausdrücklicher Nutzerfreigabe wurde die zuvor
gestoppte Prüfung fortgesetzt. Ausschließlich synthetische Daten; kein Commit,
Push oder Umzug in die Echtdatenumgebung. Produktcode blieb unverändert.

## Umgebung und Bestand

Geprüft wurde das vorhandene portable Paket `dist/MailAnalyst` aus der frischen
Python-3.11.9-Umgebung. Build, Quellsnapshot, 2.586 Paketprüfsummen und die zuvor
bestandenen 78 Tests sind im [Grundlagenbericht](2026-09-10_roadmap_foundation.md)
belegt. Diese Prüfungen wurden für die reine Bedienabnahme nicht wiederholt.
Das Laufmanifest enthält genau die externe `build_info.json` des Pakets.

Quelle: `out/roadmap-exe-check/input/`, 250 MSG und 300 EML aus zehn bzw. zwölf
Varianten, dazu eine ignorierte TXT-Datei. Sollwerte: `expected.json` im darüber
liegenden Ordner. Neues Ziel: `out/roadmap-exe-check/interactive-output/`.
Profil Analysepaket, kompakte URLs, automatische PST-Wahl, SHA-256-Prüfung aktiv.
Die separaten negativen Proben wurden in diesen Läufen nicht importiert.

## Tatsächlich bedient

- Systemcheck: 13 OK, eine Warnung wegen fehlendem optionalem libpff, keine Fehler.
  Outlook-Registrierung wird als Komponentennachweis und nicht als Importabnahme angezeigt.
- Quelle und neuen Zielordner eingegeben, Vorprüfung gestartet: 551 Quellen,
  550 OK, keine Warnungen/Fehler, eine ignorierte TXT-Datei.
- Vorprüfungsseiten 1–500 und 501–551 geöffnet. Filter „Ignoriert“ zeigt genau
  eine Zeile; Doppelklick setzt deren Auswahl nicht auf „Ja“.
- Verarbeitung gestartet, aktive Quellenprüfung mit Zähler und gesperrter
  Navigation gesehen. Ergebnis: 550 Quellen, 550 Nachrichten, null Parserfehler.
- Ergebnisseiten 1–500 und 501–550 geöffnet; letzte Weiter-Schaltfläche gesperrt.
  „Nur Fehler“ ergibt null Zeilen; Rückkehr zu allen Nachrichten funktioniert.
- Detaildialog per Doppelklick geöffnet: Betreff, vollständiger Quellenpfad und
  Status sichtbar; per Eingabetaste geschlossen.
- Zur Vorprüfung zurückgewechselt und denselben Auftrag erneut gestartet.
  Ergebnis wieder 550 Nachrichten ohne Parserfehler; Laufbericht bestätigt 550 Cachetreffer.
- Eigene Testinstanz normal geschlossen; anschließend kein MailAnalyst-Testfenster mehr offen.

## Unabhängige Dateiprüfung

Beide Läufe liegen unter dem genannten Ziel in `runs/`:

| Lauf-ID | Nachrichten | Parserfehler | Cachetreffer | Laufzeit laut Manifest |
| --- | --- | --- | --- | --- |
| `20260910T155832-0c6c50a9cd584f10b212cf4e52b3dcf0` | 550 | 0 | 0 | 4,06 s |
| `20260910T155958-e0501ae3538d44dfb0585ab96a398f7e` | 550 | 0 | 550 | 2,24 s |

Für beide Laufpakete wurden außerhalb der EXE erfolgreich geprüft:

- JSON: alle 550 Message-IDs, Betreffe, UTC-Daten, Anlageninventare und
  erwarteten Textstellen gegen die erzeugten Sollwerte; Status und Absender.
- Parquet: 550 Zeilen und identische Message-ID-Menge.
- Alle elf Exportdateien gegen Größe und SHA-256 im Manifest.
- Markdown-Dataset: 550 Indexeinträge, vorhandene Monatsdateien und Anker;
  Verweise bleiben innerhalb des Datasets.
- Ergebnisindex: 500 plus 50 Zeilen, korrekte Herkunftspfade und null Fehler.
- Quellenbericht: je 550 Audits, zunächst `parsed`, danach `cache`, jeweils
  `verified_this_run`; SHA-256 stimmt mit Vorprüfung und aktuellen Quelldateien überein.
- Laufmanifest `completed`; Optionen stimmen mit `processing_options.json`
  überein, `preflight_binding=sha256`. Vorprüfungsbericht enthält 551 Quellen,
  davon 550 ausgewählt. Alle auftragsbezogenen Systemchecks sind OK.
- Beide Logs enthalten die richtige Abschlusszusammenfassung einschließlich Cachezahl.
- Cache liegt im gewählten Zielordner; SQLite-Integritätsprüfung ergibt `ok`.

Kompakte lokale Prüfergebnisse: `out/roadmap-exe-check/interactive-verification.json`.
Die erzeugten Dateien bleiben außerhalb von Git.

## Befunde und Grenzen

In diesem Bedienumfang wurde kein neuer Funktionsfehler gefunden. Die kurzen
Läufe erlaubten keine getrennte Sichtprüfung jeder Export-/Validierungsphase;
beobachtet wurden aktive Quellenprüfung und Abschluss. Abbruch, Mehrfachstart,
Fehlerzeilen hinter Seite eins und Start aus fremdem Arbeitsverzeichnis wurden
in diesem Block nicht erneut geprüft. Dies ist keine Gesamtabnahme aller GUI-Pfade.

Echte PST-Dateien, Outlook-Sitzungen, sauberer Windows-Zielrechner und erzwungener
Offline-Betrieb bleiben ungetestet. Anlageninhalte sind synthetische Platzhalter;
der Test bestätigt deren Inventar, keine PDF-/Office-Inhaltsanalyse. Die Laufzeiten
sind lokale Beobachtungen und keine zugesicherten Leistungsgrenzen.

## Dokumentation und nächster Schritt

STATUS einschließlich REL-01 und nächstem Arbeitsblock aktualisiert. README,
Architektur, Datenmodell und Projektziele benötigen für diese reine Testfortsetzung
keine inhaltliche Änderung. Lokale Dokumentations-Dateiziele und Diff geprüft.
Als nächstes DATA-07 und EXPORT-01; die Umzugsschwelle bleibt unerreicht.
