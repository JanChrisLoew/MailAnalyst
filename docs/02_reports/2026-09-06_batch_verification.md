# MailAnalyst – Batchverarbeitung und synthetische Lastprüfung

Datum: 6. September 2026. Lokaler Änderungsstand auf Basis von `1a7fc1f`; dieser Bericht löst keinen Commit oder Push aus.

## Ergebnis und Umfang

CLI und GUI verwenden einen SQLite-Nachrichtenspeicher statt eines vollständigen Master-DataFrames. Standardbatches umfassen höchstens 500 Nachrichten und eine zusätzliche weiche Textschwelle von 8 MiB. EML-/MSG-Arbeit wird mit begrenzten Futures eingeplant; PST-Adapter liefern Nachrichten schrittweise. Alle Exportformate und die strukturierte Rückleseprüfung verarbeiten Zeilen beziehungsweise Batches. Die Monatsaufteilung und Sortierung erfolgen auf der Festplatte.

Der Cache speichert Quellenkriterien und einzelne Nachrichten getrennt (Version 2). Version 1 wird kontrolliert neu aufgebaut; Hash-/Änderungsprüfung und atomarer Cacheersatz bleiben erhalten. Manifest Version 2 verweist auf `sources.jsonl`, statt alle Quellen-Audits als Array im RAM zu sammeln. Die GUI erhält höchstens 500 Vorschauzeilen, weiterhin vollständige Nachrichten-/Fehlerzahlen und Ergebnis-Scrollbars.

## Automatisierte Prüfung

Windows, Python 3.11, vorhandene Repository-Umgebung `.venv`. Ausschließlich synthetische Daten.

| Prüfung | Ergebnis |
| --- | --- |
| `python -m unittest discover -v` | 52 Tests bestanden, keine übersprungenen Tests; 9,64 Sekunden im abschließenden Lauf. |
| `python -m compileall -q mailanalyst tests scripts mail_analyst.py mail_analyst_gui.py` | Erfolgreich. |
| `python -m pip check` | Keine beschädigten Abhängigkeiten. |
| `git diff --check` | Erfolgreich. |
| `build_exe.ps1` | Windows-Onedir-Paket erfolgreich gebaut; Exitcode 0. |
| Bedienprüfung der gebauten EXE | Nicht ausgeführt: Die verfügbaren Computer-Use-Werkzeuge bieten in dieser Sitzung keine native Windows-App-Steuerung. |

Neue Tests prüfen Cachemigration, Änderungen und beschädigte Einzelzeilen, tatsächlichen synthetischen EML-Import, Exportvergleich mit der materialisierten Referenz, späte Parquet-Typmischungen, Batch-/Vorschaubegrenzung, große CSV-Zellen, JSON-Chunkgrenzen, Monatsanker und Pfadbegrenzung. CSV-/Excel-Formelschutz wird auch auf dem neuen Exportpfad geprüft. Bestehende Export-Snapshots wurden nicht geändert.

Abbruch während Verarbeitung oder Export erhält bestehende veröffentlichte Daten. Archive werden bei erkannten Quellenänderungen verworfen; bereits gelesene Nachrichten mit späterem abgefangenem Traversierungsfehler erhalten zusätzlich eine Fehlerzeile. PST-Testdoubles prüfen Lazy Reading, Generatorabschluss, COM-Abmeldung und das ausschließliche Entfernen selbst hinzugefügter Outlook-Stores. Das sind keine realen PST-Importnachweise.

Der Python-Tk-Test durchläuft Systemcheck, Vorprüfung, Verarbeitung und Ergebnisanzeige mit zwei synthetischen EMLs. Ein zusätzlicher GUI-Test bestätigt maximal 500 Tabellenzeilen bei separat übergebenen Gesamtzahlen. Beim gesamten Tk-Testlauf erscheinen bekannte ThemeChanged-Meldungen während zerstörter Testfenster; die Tests bestanden ohne übersprungene GUI-Abläufe. Keine interaktive Testinstanz wurde geöffnet oder zurückgelassen.

## Lastmessungen

Reproduzierbarer Treiber: [scripts/benchmark_batches.py](../../scripts/benchmark_batches.py), Aufruf über `python -m scripts.benchmark_batches`. Jeder Datensatz läuft in einem neuen Prozess; frischer Import und Cachelauf folgen im selben Prozess. Jeder Durchlauf erzeugt und validiert Parquet, JSON und Markdown-Monatsordner, prüft Nachrichtenzahlen und Vorschau, erstellt Quellen-Audit und Exporthashes und veröffentlicht ein Laufpaket.

Die Nachrichten enthalten etwa 2,2 KiB gleichförmigen synthetischen Plaintext. Wegen der Roh-/Clean-/Aliasfelder ist eine gespeicherte Nachrichtenzeile etwa 9 KiB groß. Diese Gleichförmigkeit repräsentiert weder reale Anlagen noch die Formatvielfalt produktiver Postfächer. Die EML-Bestände liegen in einem Ordner, der Archiv-Double liefert einen einzigen Stream. Nachrichtenerzeugung wird getrennt gemessen und ist nicht Teil der folgenden Laufzeiten.

| Synthetischer Bestand | Frischer Lauf | Cachelauf | Peak frisch / nach Cache | Cachetreffer |
| --- | --- | --- | --- | --- |
| 1.000 echte EML-Dateien | 3,99 s | 1,09 s | 148,1 / 167,4 MiB | 1.000 Quellen |
| 50.000 echte EML-Dateien | 178,41 s | 71,55 s | 242,6 / 334,4 MiB | 50.000 Quellen |
| 100.000 Nachrichten, PST-Importer ersetzt durch Generator | 46,03 s | 49,20 s | 232,1 / 265,2 MiB | 1 Quelle |

Gemessen wird `PeakWorkingSetSize` über die Windows-Prozess-API: der bisherige Spitzenarbeitssatz des jeweiligen Python-Prozesses, kein Python-Heap-Limit und kein Gesamtspeicher einschließlich Betriebssystem-Dateicache. Cachelauf-Peaks sind kumulativ. Hintergrundlast war nicht isoliert; während Teilen der Abschlussmessung liefen auch Tests beziehungsweise Build. Die Zahlen sind ein technischer Funktionsnachweis, keine garantierten Laufzeiten und kein sauber isolierter Performancevergleich.

Die abschließenden EML-Messungen und der 100.000er-Stream enthalten vollständiges inkrementelles Parquet-Rücklesen. Ein vorläufiger 50.000er-Lauf mit ausschließlicher Parquet-Metadatenprüfung wurde durch die hier berichtete Abschlussmessung ersetzt. Alle Läufe meldeten die erwartete Nachrichtenanzahl und null Parserfehler. Beim 100.000er-Stream betrug der größte Importbatch 500 Zeilen beziehungsweise 4.628.500 serialisierte Bytes. EML-Quellen liefern jeweils eine Importzeile; Parquet gruppiert sie beim Export in Batches.

Lokale Rohmessungen und Laufpakete liegen ausschließlich unter den ignorierten Ordnern `out/batch-benchmark-eml-1000-final`, `out/batch-benchmark-eml-50000-final` und `out/batch-benchmark-archive-100000`. Logs, Maildateien, Cache und Exporte werden nicht Teil des öffentlichen Repositorys.

## Grenzen und nächste Abnahmen

- Reale MSG-/PST-Importer, Outlook-Veränderungen an Archiven und Zielhardware bleiben praktisch abzunehmen. Der 100.000er-Test ersetzt ausdrücklich den PST-Importer.
- Keine automatische Wiederaufnahme nach Prozessabbruch. Ein unvollständiger Lauf bleibt unvollständig; eine Arbeitsdatei kann zurückbleiben. Der Cache umfasst weiterhin die Quellen des letzten erfolgreich verarbeiteten Laufs.
- Quellpfade, GUI-Vorprüfungsdaten, Rekursion, Einzelmails und Fremdbibliotheken sind weiterhin größenabhängig. Die Bytegrenze ist weich und kann um eine Einzelzeile überschritten werden. Arbeitsdatei, Cache und mehrere Exporte benötigen zusätzlichen Plattenplatz.
- Parquet verwendet ein global stabiles Schema; gemischte Zahlen-/Textfelder werden zu Text. JSON bewahrt die skalaren Typen. Die DataFrame-Kompatibilität für kleine Python-Aufrufe bleibt materialisierend und hat weiterhin die frühere Typableitung.
- Frühe Outlook-Fehler ohne verfügbare RootFolder-Referenz sind noch nicht vollständig abgesichert. Die vollständige EXE-Bedienprüfung steht aus; ein Build ist kein Bediennachweis.

## Dokumentationsprüfung

README, Architektur, Datenmodell, STATUS, technische Referenzgröße in PROJECT_GOALS und der Repository-Prüfskill wurden mit dem tatsächlichen Diff abgeglichen und aktualisiert. Lokale Links und Abschnittsverweise der betroffenen Dokumente wurden geprüft. Historische Berichte bleiben unverändert. Betriebsinterne Herleitungen und persönliche Angaben wurden nicht in die neuen Dokumente übernommen.
