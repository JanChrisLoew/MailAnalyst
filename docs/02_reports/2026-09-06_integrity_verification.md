# Integritätsblock: Cache, Quellenprüfung und Laufpakete

Stand: 6. September 2026. Ausgangspunkt: Commit `bbb8611`; Umsetzung lokal, ohne Commit/Push. Ausschließlich synthetische Maildaten verwendet.

## Änderungen

- DATA-02: SQLite-Cache mit versionierten JSON-Einträgen und Strukturprüfung. Pickle wird nicht mehr gelesen. Ungültige Caches werden neu aufgebaut, bestehende Cachedateien erst nach vollständiger Quellverarbeitung ersetzt.
- DATA-03: Cachekriterien enthalten Zeitzone, Schema-/Parserrevision und aufgelöstes PST-Backend. Neue Importe und strenge Cachetreffer werden vor/nach Verarbeitung gehasht. Pro Quelle dokumentiert das Manifest frische Prüfung oder ungeprüfte Hashübernahme.
- DATA-04/05: Eindeutige Laufordner, Manifest und Exportpaket. Temporäre Einzelexporte werden zurückgelesen und auf Zeilenzahl geprüft; Markdown-Indizes auf Anzahl und Referenzen. Erst anschließend wird das Paket veröffentlicht und abgeschlossen. Explizite CLI-Ziele bleiben zusätzliche Kopien; alte Markdown-Verzeichnisse bleiben als `.previous-<UUID>` erhalten.
- LOG-01: Eigene Laufprotokolle einschließlich Cachezählung und Zusammenfassung. GUI zeigt den konkreten Laufordner an.
- Nachrichtenexportspalten bleiben unverändert. Nur Markdown-Indexpfade wechseln zu `/`. Der historische Snapshot wurde nicht verändert; der Test normalisiert ausschließlich diese beabsichtigte Indexpfadänderung und vergleicht JSON-Indizes strukturell.

## Ausgeführte Prüfungen

Windows, lokale Python-3.11-Umgebung des Projekts:

- `python -m unittest discover -v`: 26 Tests bestanden; keine übersprungenen GUI-Tests.
- Bestehende Parser-/Exportregression, beide CLI-Einstiege, sämtliche GUI-Profile und echter Tkinter-Ereignisablauf mit synthetischen EMLs.
- Neue Tests: beschädigte/inkompatible Cachedateien und JSON-Strukturen, unangetastete Pickledateien, Zeitzoneninvalidierung, gleiche Größe/Änderungszeit bei geändertem Inhalt, automatische Backendänderung und leeres PST mit Testdoubles, Quellenmutation während Parsing, fehlgeschlagener Cacheersatz.
- Laufprüfungen: wiederholte getrennte Pakete, Exporthashes, kopierte Markdown-Referenzen, Export-/Validierungsfehler, leere Pakete, unvollständiger Manifestzustand und erhaltene CLI-Vorgängerverzeichnisse.
- `compileall`, `pip check`, 200-Zeilen-/Importarchitekturprüfung und `git diff --check` bestanden.
- `build_exe.ps1`: Windows-EXE erfolgreich gebaut. Keine vollständige EXE-Bedienprüfung: native Windows-Bedienwerkzeuge waren in dieser Sitzung nicht verfügbar. Keine Test-EXE gestartet oder offengelassen.

## Grenzen

Keine reale MSG-/PST-Abnahme, keine Großmengenmessung und kein nachgewiesener GitHub-CI-Lauf. SQLite ersetzt das Speicherformat; die Pipeline hält weiterhin den vollständigen Datenbestand im RAM. Automatischer Abbruch, GUI-Mehrfachstarts, Bindung der Vorprüfung an denselben Dateistand und Formelinterpretation sind weiterhin offene Folgearbeiten.

Vorher-/Nachher-Hashes sind keine unveränderlichen Quellsnapshots; zurückgesetzte Zwischenänderungen sind nicht vollständig ausgeschlossen. Outlook kann PST-Dateien verändern, sodass die neue Integritätsprüfung einen solchen Lauf ablehnt; praktische Abnahme erforderlich. Exportvalidierung prüft Lesbarkeit, Anzahl und Markdown-Referenzen, keine vollständige fachliche Gleichwertigkeit aller Formate. Manifeste sind nicht signiert. Stromausfall-Dauerhaftigkeit und gemeinsame Atomarität über mehrere explizite CLI-Ziele werden nicht zugesichert.

## Dokumentationsprüfung

README, Architektur, Datenmodell, Status und Repository-Prüfskill wurden mit dem neuen Verhalten abgeglichen und aktualisiert. Fachliche Projektziele bleiben unverändert. Historische Berichte behalten ihren zeitlichen Bezug. Geänderte lokale Dokumentationsverweise wurden geprüft.
