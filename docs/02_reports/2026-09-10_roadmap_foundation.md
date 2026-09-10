# Versionsgrundlage und auftragsbezogene Prüfungen

Stand: 10. September 2026. Umsetzung der unmittelbar nächsten Roadmap-Schritte,
synthetische Daten, kein Commit/Push und kein Umzug in die Echtdatenumgebung.

## Änderungen

- App-Version `0.5.0-dev.1` zentral in `version.py`, CLI `--version`, Fenstertitel
  und Laufmanifest. Entwicklungsstarts melden sich als `development`.
- Windows-Lockdatei mit direkten und transitiven Paketversionen, Python 3.11.9
  in lokaler Prüfung und CI. Mindestanforderungsdateien bleiben bestehen.
- Build mit eingebetteter und externer `build_info.json`, Quellrevision,
  Änderungsstatus, Quellbaum-Hash, Python und Paketversionen. Lokaler Quellsnapshot
  unter `out/build-metadata/source_snapshot.zip`; Paketmanifest mit Datei-Hashes.
- GUI-Vorprüfung inventarisiert nicht unterstützte Dateien. Der Zielteilbaum wird
  ausgeschlossen; Verzeichnis-Symlinks werden nicht verfolgt. Ignorierte Dateien
  können nicht zur Verarbeitung ausgewählt werden. Leere unbekannte Dateitypen
  sind ebenfalls ignoriert statt fälschlich defekte Maildateien.
- Unterstützte Quellen werden per Größe, Änderungszeit und SHA-256 an die
  Vorprüfung gebunden, direkt vor dem jeweiligen Import/Cachelesen. Änderungen
  führen zum Laufabbruch mit Hinweis auf erneute Vorprüfung. Das gilt auch bei
  wiederhergestellter Größe und Änderungszeit. Keine Quellkopie/Dateisperre.
- CLI und direkte Service-Aufrufe ohne vorherige Vorprüfung prüfen ihre Auswahl
  neu. CLI behält die bisherige Auswahl unterstützter Dateitypen bei. GUI zeigt
  zusätzlich ignorierte Quellen. Vorprüfungs- und auftragsbezogene Systemberichte
  liegen im jeweiligen Laufordner. `preflight_binding=sha256` dokumentiert den
  Pflichtmodus; `--hash-check` bleibt kompatibel. Direkte Kernaufrufe können
  weiterhin ausdrücklich den schnellen Cachemodus nutzen.
- Benötigte Module werden abhängig von Quellformat und Ausgabe geprüft. Reale
  Ziel-/Cache-/Arbeitsordner erhalten temporären Schreibtest und Platzprüfung.
  Weniger als 16 MiB blockiert; eine Reserve von sechs Quellgrößen ist lediglich
  eine Warnschwelle. Outlook-Registrierung ist kein Nachweis einer nutzbaren Sitzung.

## Verifikation

- Neun neue Tests für Version/Manifest, gebündelte Metadaten, Komponentenwahl,
  Schreib-/Platzfehler, Inventar, Quellenänderung, fehlende Auswahlbindung,
  Archiv-Fingerabdruck vor Backendaufruf und laufbezogene Berichte/Cacheprüfung.
- Vorhandener GUI-Test an die neue Inventarsemantik angepasst: zwei Mails plus
  ignorierte TXT-Datei; deren Auswahl bleibt gesperrt. Kein Vergleichssnapshot geändert.
- Komplette Suite aus frischer `out/baseline-venv`: **78 Tests erfolgreich**,
  finaler Lauf 29,4 Sekunden; keine Skips. Python-Tkinter-Workflow enthalten.
- Frische Installation aus `requirements-windows-lock.txt` erfolgreich. Der erste
  Versuch scheiterte an der eingeschränkten Paketverbindung; der freigegebene
  Netzwerkaufruf installierte die fixierten Pakete erfolgreich. `pip check` und
  Kompilierung bestanden.
- `build_exe.ps1 -PythonPath .\out\baseline-venv\Scripts\python.exe` erfolgreich.
  Alle **2.586 Paketdateien** separat gegen Größe und SHA-256 geprüft. Interne und
  externe Buildmetadaten identisch. Quellsnapshot-Hash entspricht dem Buildhash.
- Build meldet lokale Änderungen (`source_dirty=true`); kein freigegebener Tag.
  Der Snapshot erhält genau den Buildstand, auch wenn spätere Prüfdokumentation
  im Arbeitsverzeichnis ergänzt wird.
- CI-Konfiguration ergänzt; kein neuer Remote-CI-Lauf behauptet.

## Interaktive EXE-Grenze

Die gebaute EXE wurde gestartet; ein Fenster mit Titel `MailAnalyst 0.5.0-dev.1`
wurde gefunden. Beim ersten Zustandsabruf stoppte der Nutzer Computer Use mit
Escape. Danach erfolgte keine weitere UI-Steuerung. Somit **keine vollständige
EXE-Funktionsabnahme**, auch keine bestätigte Systemcheck-/Ergebnisanzeige.
Das gestartete Fenster wurde nach dem Stopp nicht automatisch geschlossen.

Für die spätere Abnahme vorbereitet: `out/roadmap-exe-check/input/` mit 550
synthetischen MSG/EML und einer ignorierten TXT-Datei, Sollwerte daneben. Dieser
Bestand wurde in diesem Block nicht über die EXE verarbeitet. Ein sauberer
Windows-Zielrechner, tatsächliche PSTs und Offline-Abnahme bleiben ebenfalls offen.

## Dokumentationsprüfung und nächste Arbeit

README, Architektur, Datenmodell, STATUS und Roadmap an die Implementierung
angepasst. Releasehinweise ergänzt. Projektziele unverändert. Lokale Dateiverweise
werden mit `scripts.check_doc_links` geprüft; Abschnittsanker nicht eingeschlossen.
Nächste Arbeit: vollständige EXE-Bedienabnahme fortsetzen, danach DATA-07/EXPORT-01.
Die Umzugsschwelle 0.9.0-rc.1 ist nicht erreicht.
