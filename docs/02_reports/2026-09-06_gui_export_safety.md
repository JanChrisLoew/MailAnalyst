# GUI-Steuerung und sichere Tabellenansichten

Stand: 6. September 2026. Aufbauend auf dem lokalen Integritätsblock; keine Commits/Pushs. Ausschließlich synthetische EMLs und gezielte Testdoubles verwendet.

## Umgesetzter Umfang

GUI-01: Zentrale Einzeljobsperre für Systemcheck, Vorprüfung und Verarbeitung. Eingaben und Navigation werden während eines Jobs gesperrt. Wiederholte Startaufrufe werden abgewiesen; neue Läufe sperren veraltete Ergebnisansichten.

GUI-02: Nicht als Daemon gestartete Worker, kooperatives Abbruchsignal und geordnetes Fensterschließen. Fortschritts-, Quellen-/Hash- und Exportgrenzen prüfen den Abbruch. Die Paketveröffentlichung hat eine synchronisierte Grenze: Vorher angeforderter Abbruch erzeugt `cancelled`, später angeforderter Abbruch lässt den Abschluss fertig laufen. Schließen wartet auf das tatsächliche Workerende, unterdrückt UI-Abschlusscallbacks und gibt Log-Handler/Timer frei.

DATA-06: CSV-Zeichenfolgen mit formelverdächtigen Anfängen erhalten ein Apostroph, einschließlich führender Leer-/Steuerzeichen. Das gilt für volle CSV-Sichten, Listen, Markdown-Indizes und Prüfberichte. Excel-Zeichenfolgen werden explizit als Text gespeichert. Masterbestand, Cache, JSON, JSONL und Parquet bleiben unverändert.

## Verifikation

- 39 automatisierte Tests bestanden, einschließlich aller bisherigen 26 Regressionstests. Keine übersprungenen GUI-Tests.
- Live-Tk-Tests mit kontrolliert wartendem Parser: Doppeltstart, Navigation-/Startguards, Abbruch, Neustart sowie Fensterschließen vor Parserende und nach tatsächlichem Threadende.
- Vorprüfungsabbruch mit anschließendem Neustart; Workerfehler mit Freigabe und erneutem Auftrag; Schließen vor dem geplanten automatischen Systemcheck.
- Kernprüfungen: Abbruch am Fortschrittscheckpoint erhält den bisherigen Cache; Abbruch zwischen Exporten veröffentlicht kein Teilpaket; Veröffentlichung und spätere Abbruchanforderung sind eindeutig geordnet; Hashschleife prüft das Signal.
- Echte CSV-Dateien zurückgelesen und tatsächliche XLSX-Zelltypen mit openpyxl kontrolliert: keine Formeln/Hyperlinks, negative Zahlen bleiben numerisch, Texte bleiben Text. JSON-/Parquet-Masterdaten unverändert. CSV-Index und CSV-Prüfberichte ebenfalls geprüft.
- Historische Exportvergleichsdaten unverändert; normale synthetische Exportinhalte bleiben kompatibel.
- `compileall`, `pip check`, Architektur-/200-Zeilen-Prüfung und `git diff --check` bestanden.
- Windows-EXE mit `build_exe.ps1` erfolgreich gebaut. Keine vollständige Bedienprüfung der gebauten EXE, da native Windows-Bedienwerkzeuge in dieser Sitzung nicht verfügbar waren. Keine EXE-Testinstanz offengelassen.

## Grenzen

Kooperativer Abbruch beendet keinen laufenden Fremdparser gewaltsam. Ein blockierender PST-/Outlook-/Bibliotheksaufruf kann deshalb Abbruch und Schließen verzögern. Es gibt keine Prozessisolation oder feste Abbruchzeit. Ein vor einem späteren Exportabbruch fertig geschriebener Cache bleibt nutzbar. CLI-Prozesssignale sind nicht Teil der neuen GUI-Abbruchsteuerung.

CSV ist eine Sichtdarstellung mit Schutzpräfixen; für unveränderte maschinelle Weiterverarbeitung JSON/Parquet/JSONL verwenden. Excel bleibt ein Sichtformat mit Zelllängenbegrenzung; CR-Zeichen erschienen im getesteten XLSX-Rücklesen als LF. Keine Live-Excel-Bedienprüfung. Reale MSG-/PST-Archive, Großmengen und GitHub-CI weiterhin nicht abgenommen.

## Dokumentationsprüfung

README, Architektur, Datenmodell und Status mit dem implementierten Verhalten abgeglichen und aktualisiert; lokale Dokumentationsverweise geprüft. PROJECT_GOALS und der Repository-Prüfskill bleiben gültig: keine neuen fachlichen Anforderungen beziehungsweise kein geänderter Build-/Prüfbefehl. Historische Prüfberichte bleiben zeitlich eingeordnet.
