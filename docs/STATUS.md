# MailAnalyst – aktueller Arbeitsstand

Stand: 11. September 2026. Diese Datei ist die aktuelle Übersicht; Review- und Prüfberichte dokumentieren den jeweiligen historischen Stand.

Die [Versions- und Ausbauplanung](01_guides/ROADMAP.md) schlägt 0.5.0 bis 1.0.0
mit konkreten Abnahmekriterien vor. Nutzerfestlegung: Umzug zum Echtdaten-Test
erst nach produktionsnaher synthetischer Abnahme. Versionsnummern und Detailumfang
sind Planungsstand, keine bestehenden Releases. Umzug und Echtdatenverarbeitung
wurden nicht gestartet; Hardware- und PST-Entscheidungen bleiben offen.

## Erreichter Stand

Der aktuelle Entwicklungskandidat ist **0.7.0-dev.1**. Eine sechste synthetische
MSG enthält eine echte eingebettete Nachricht als OLE-Unterstruktur. MailAnalyst
inventarisiert Namen und Anzahl, exportiert den inneren Inhalt bewusst noch nicht
und weist dies mit `embedded_message_not_extracted` aus. Nachrichtenvertrag 2
und Parserrevision 3 verhindern eine stille Wiederverwendung älterer Cachezeilen.
Der vollständige Standardlauf bestand danach 85 Tests mit einem erwarteten
optionalen PST-Skip; der tatsächliche PST-Dateitest war zuvor separat erfolgreich.
Nach DEC-02 wurde libpff als Windows-3.11-Laufzeitabhängigkeit und PyInstaller-
Modul aufgenommen. Der 0.7.0-dev.1-Build enthält `pypff` und beide LGPLv3+-
Lizenztexte; echter PST-Lauf und Build waren erfolgreich. Eine vollständig
bediente PST-EXE-Abnahme bleibt offen.

Der erste 0.7.0-Prüfschritt liest eine gültige öffentliche PST-Referenzdatei mit
dem tatsächlichen libpff-Backend. Zwei Nachrichten in zwei bekannten Ordnern,
Datum, Betreff, Backend, strukturierte Warnungen, Analysepaket und anschließender
Cachetreffer wurden geprüft; der SHA-256 der Quelle blieb vor und nach beiden
Läufen gleich. Das optionale Windows-Test-Wheel ist mit Version und Hash separat
fixiert und bleibt außerhalb von Standardinstallation und Build. Weil die Datei
nicht vom Projekt selbst synthetisch erzeugt wurde, ist dies noch keine vollständige
PST- oder 0.7.0-Abnahme. [Nachweis](02_reports/2026-09-11_libpff_pst_verification.md).

Die beim Gesamttest sichtbar gewordene native Python-Ausnahme `0x80000003`
stammte aus verspäteter Tkinter-Objektfreigabe auf einem Workerthread. GUI-Tests
lösen ihre App-Referenzen nun beim Aufräumen und erzwingen die Garbage Collection
noch im GUI-Thread. Der kritische GUI-/Korpus-Ablauf sowie zwei aufeinanderfolgende
vollständige Testprozesse liefen danach ohne Tcl-Abbruch oder Fehlerdialog durch.
[Nachweis](02_reports/2026-09-11_libpff_pst_verification.md#tkinter-testprozess).

Der Datenvertrags-/Exportblock vom 11. September liefert **0.6.0-dev.1**.
Nachrichtenvertrag Version 1 prüft Pflichtbezüge, skalare Feldtypen, Parserstatus
und UTC-Zeitstempel; fachlich mögliche Lücken erscheinen mit stabilen Warncodes
im Laufmanifest und in `quality_warnings.jsonl`. libpff kopiert reine Anzeigenamen
nicht mehr als SMTP-Adressen. Markdown trennt Mailtext als Zitatbereich und
maskiert strukturwirksame Metadaten; XML erhält gültige Zeichen außerhalb der BMP.
83 automatisierte Tests, Kompilierung, Abhängigkeits- und Diffprüfung sowie der
Windows-Build waren erfolgreich. Native App-Steuerung stand für eine neue
interaktive EXE-Bedienung nicht zur Verfügung. [Nachweis](02_reports/2026-09-11_data_contract_export_hardening.md).

Der erste Roadmap-Umsetzungsblock liefert **0.5.0-dev.1** mit zentraler Version,
Buildmetadaten, lokalem Quellsnapshot und Paketprüfsummen. Eine frische Umgebung
mit der Windows-Lockdatei bestand 78 Tests; der daraus erstellte Build und 2.586
Paketdateien wurden geprüft. GUI-Inventarisierung, SHA-256-Vorprüfungsbindung und
auftragsbezogene Ziel-/Komponentenprüfungen sind umgesetzt.
[Umsetzungsnachweis](02_reports/2026-09-10_roadmap_foundation.md).
Die anschließend freigegebene interaktive EXE-Prüfung bestand den Analysepaket-
Workflow mit 550 synthetischen MSG/EML und einen Wiederholungslauf mit 550
verifizierten Cachetreffern, jeweils ohne Parserfehler. Vorprüfung, Seitenwechsel,
Filter und Quelldetails bedient; Exporte und Laufberichte unabhängig geprüft.
[EXE-Prüfbericht und Grenzen](02_reports/2026-09-10_interactive_exe_verification.md).

Der anschließende gemischte Testblock vom 10. September erweitert den Bestand auf
zehn MSG- und zwölf EML-Varianten sowie acht separate negative Dateiproben.
Ein dauerhaft erzeugtes Analysepaket mit 550 Nachrichten (250 MSG, 300 EML)
enthält keine Parserfehler; Sollfelder, Parquet-IDs und elf Exporthashes wurden
unabhängig geprüft. 69 automatisierte Tests bestanden. Produktcode blieb in
diesem Block unverändert. [Nachweis](02_reports/2026-09-10_mixed_corpus_verification.md).

Der synthetische Importblock vom 10. September ergänzt vier echte Unicode-MSG-Dateien mit erfundenen Inhalten, Sollwerten und wiederholbarem Generator. Die tatsächliche Parserprüfung fand und behob verlorene MSG-Versanddaten; Parserrevision 2 erzwingt den Neuimport älterer Cacheeinträge. 65 erfolgreiche Tests einschließlich Feld-, Export- und Cacheprüfungen sowie der erfolgreiche Windows-Build sind im [Prüfbericht](02_reports/2026-09-10_synthetic_import_verification.md) dokumentiert. PST-Dateiprüfungen bleiben offen: libpff fehlt lokal und Outlook-COM war nicht erreichbar. Es wurden keine realen Mailbestände verarbeitet.

CLI und GUI verwenden seit dem Batchblock vom 6. September einen SQLite-Nachrichtenspeicher mit begrenzten Batches und inkrementellen Exporten. PST-Adapter liefern Nachrichten als Iteratoren; die GUI erhält höchstens 500 Vorschauzeilen mit Gesamtzahlen und Scrollbars. Laufmanifest Version 2 verweist auf eine separat geschriebene `sources.jsonl`. Bestehende Cacheversion 1 wird einmalig neu aufgebaut.

Der anschließende GUI-Batchblock ergänzt Phasen, Nachrichtenzähler, Laufzeit und begrenzte Seiten mit Filtern. Ergebnisse einschließlich später Fehler sind über einen kompakten Laufindex erreichbar. 58 automatisierte Tests bestanden einschließlich Python-GUI; außerdem lief der vollständige Python-GUI-Workflow mit 50.000 synthetischen EMLs erfolgreich durch. Der abschließende Windows-Build war erfolgreich. Nachweis: [GUI-Batchprüfung](02_reports/2026-09-06_gui_batch_verification.md). Die vorherige Batchprüfung umfasste 52 Tests und einen erfolgreichen Windows-Build. Nachweis: [Batchprüfung](02_reports/2026-09-06_batch_verification.md). Die früheren [GUI-/Exportprüfungen](02_reports/2026-09-06_gui_export_safety.md) und [Integritätsprüfungen](02_reports/2026-09-06_integrity_verification.md) bleiben historische Nachweise. Echte MSG-/PST-Archive stehen weiterhin aus. Technischer Referenzbestand: 50.000 Nachrichten; Zielhardware und zulässige Laufzeit bleiben offen.

Das UI-/UX-Review vom 7. September vereinheitlicht Sprache und Schrittbezeichnungen, reduziert dekorative Elemente, klärt Laufordner und Tabelleninteraktion und ergänzt Tastaturbedienung. Die interaktiv gefundenen Restfehler wurden anschließend behoben: Ergebnisinhalt und Navigation wechseln gemeinsam, Kernspalten sind bei Standardgröße vollständig sichtbar, Dialoge sind am Hauptfenster verankert und die Konfigurationsaktion bleibt bei Mindestgröße erreichbar. 61 automatisierte Tests, Kompilierung, Abhängigkeitsprüfung, Windows-Build und ein vollständig bedienter synthetischer EXE-Lauf waren erfolgreich. Nachweis: [UI-/UX-Review](02_reports/2026-09-07_ui_ux_review.md).

Die Batch-, GUI-, Import- und Versionsblöcke werden gemeinsam als geprüfter Entwicklungsstand versioniert. Den aktuellen Commit- und Synchronisationsstand mit `git status` und `git log` feststellen. Auf Nutzerwunsch vom 10. September 2026 ist der GitHub-CI-Workflow entfernt. Tests, Dokumentationsprüfung und Builds erfolgen lokal; frühere CI-Berichte bleiben historische Nachweise. Fachlicher Auftrag: [Projektziele](../PROJECT_GOALS.md).

## Prioritäten und Statusregeln

P1: vor einem Pilot mit großen Archiven. P2: vor breiter Verteilung beziehungsweise für zuverlässige Weiterentwicklung. P3: spätere fachliche Erweiterung oder noch zu priorisierende Infrastruktur.

Statuswerte: **erledigt**, **teilweise**, **offen**, **Entscheidung offen**. „Erledigt“ bezieht sich jeweils nur auf den beschriebenen Umfang. IDs bleiben erhalten; beim Abschluss Nachweis und Datum ergänzen. Neue Aufgaben bekommen neue IDs. Detaillierte Gründe stehen im [Review vom 4. September](02_reports/2026-09-04_review_report.md).

## Struktur, Tests und Dokumentation

| ID | Priorität | Status | Umfang / nächster Schritt |
| --- | --- | --- | --- |
| REPO-01 | P2 | erledigt | Modularisierung und 200-Zeilen-Prüfung; siehe Refactoring-Abnahme vom 5. September. |
| REPO-02 | P2 | erledigt | Lokale Tests erfolgreich. GitHub-CI am 10. September 2026 auf Nutzerwunsch entfernt; künftige Abnahmen lokal. Frühere GitHub-Läufe sind nur historische Nachweise. |
| REPO-03 | P2 | erledigt | Agent-Einstieg, aktueller Status, Datenmodell und Repository-Prüfskill angelegt; Dokumentationsverweise geprüft. Am 5. September 2026 die verbindliche [Dokumentationsprüfung nach Änderungen](01_guides/ARCHITECTURE.md#dokumentationsprüfung-nach-änderungen) ergänzt und über AGENTS.md eingebunden. |
| REPO-04 | P3 | erledigt | Windows-/Python-3.11.9-Baseline mit direkten/transitiven Versionspins; in frischer venv installiert, getestet und gebaut. Keine Wheel-Hashes/byteidentischen EXEs zugesichert. [Nachweis](02_reports/2026-09-10_roadmap_foundation.md). |
| REPO-05 | P3 | teilweise | Lokale Dokumentations-Dateiziele automatisiert geprüft; einheitliche Formatierung und Abschnittsanker bleiben offen. [Nachweis](02_reports/2026-09-10_roadmap_foundation.md). |
| REPO-06 | P2 | erledigt | Bereinigung am 5. September 2026: alte Prüf-Kompatibilitätsmodule und CLI-Funktions-Reexports entfernt; Tests importieren direkt aus dem Paket. Berichte nach `docs/02_reports/` verschoben, README und Prüfskill aktualisiert, drei temporäre Prüfverzeichnisse entfernt. Zwölf Tests einschließlich CLI und Python-GUI bestanden; Skill validiert. Keine erneute EXE-Abnahme, da deren Paketimporte und Ressourcen unverändert sind. |
| REPO-07 | P1 | erledigt | Öffentliche Commitidentität auf GitHub-Benutzername/Noreply umgestellt, bestehende Historie entsprechend bereinigt und betriebliche Kontextangaben neutralisiert. Ausschlussregeln und Veröffentlichungshinweise ergänzt. Externe Kopien/Caches sind nicht kontrollierbar. [Nachweis](02_reports/2026-09-06_public_repository_privacy.md). |

Namenskonvention am 5. September 2026 umgesetzt: gepflegte Beschreibungen unter `01_guides/`, datierte Berichte unter `02_reports/`; siehe [verbindliche Namensregeln](01_guides/ARCHITECTURE.md#namenskonvention-und-ordnerreihenfolge). Dokumentation und Agent-Verweise wurden auf die neuen Pfade abgestimmt. Technische Paket- und Werkzeugnamen bleiben unverändert.

## Integrität und Laufstruktur

| ID | Priorität | Status | Umfang / nächster Schritt |
| --- | --- | --- | --- |
| DATA-01 | P1 | erledigt | GUI-Standardcache im Zielordner; EXE-Lauf und alle GUI-Profile am 5. September geprüft. CLI-Pfadwahl bleibt unverändert. |
| DATA-02 | P1 | erledigt | SQLite mit versionierten JSON-Einträgen, kontrollierter Neuaufbau bei Beschädigung/Inkompatibilität und atomarer Cacheersatz. Alte Pickles bleiben ungelesen. Nachweis: Integritätsprüfung vom 6. September. |
| DATA-03 | P1 | erledigt | Cachekriterien einschließlich Zeitzone/Backend; Hashprüfung vor/nach Import und expliziter Prüfstatus im Manifest. Grenzen ohne Quellsnapshot dokumentiert; echte PST-Abnahme bleibt IMPORT-01. Nachweis: Integritätsprüfung vom 6. September. |
| DATA-04 | P1 | erledigt | Eindeutige Laufpakete mit Manifest, Fehler-/Abschlussstatus und getrennten Exporten. Explizite CLI-Ziele sind zusätzliche Kopien. Nachweis: Integritätsprüfung vom 6. September. |
| DATA-05 | P1 | erledigt | Temporäre Einzelexporte mit Rücklese-/Anzahlprüfung, Markdown-Indexprüfung und Paketveröffentlichung erst nach Validierung. Keine gemeinsame atomare Transaktion über CLI-Kompatibilitätsziele. Nachweis: Integritätsprüfung vom 6. September. |
| DATA-06 | P1 | erledigt | CSV-Sichtausgaben einschließlich Indizes/Prüfberichte erhalten Schutzpräfixe; Excel-Zeichenfolgen werden als Text gespeichert. Master-/JSON-/Parquet-Daten bleiben unverändert. Nachweis: GUI-/Exportprüfung vom 6. September. |
| DATA-07 | P2 | erledigt | Nachrichtenvertrag Version 2 erzwingt Pflichtbezüge, Feldtypen, Parserstatus und UTC-Annahme; stabile Warncodes einschließlich nicht exportierter eingebetteter Nachrichten werden laufbezogen als JSONL nachgewiesen. [Nachweis](02_reports/2026-09-11_data_contract_export_hardening.md), [Erweiterung](02_reports/2026-09-11_libpff_pst_verification.md#ergänzende-msg-prüfung). |

## GUI und Prüfungen

| ID | Priorität | Status | Umfang / nächster Schritt |
| --- | --- | --- | --- |
| GUI-01 | P1 | erledigt | Zentrale Einzeljobsperre, gesperrte Navigation/Eingaben und Startguards; frühere Ergebnisse bei neuen Läufen gesperrt. Doppeltstart und Neustart im Tk-Test geprüft. Nachweis: GUI-/Exportprüfung vom 6. September. |
| GUI-02 | P2 | erledigt | Kooperativer Abbruch, nicht als Daemon gestarteter Worker und Warten beim Schließen; keine erzwungene Unterbrechung von Bibliotheksaufrufen. Abbruch-/Veröffentlichungsgrenze synchronisiert. Nachweis: GUI-/Exportprüfung vom 6. September. |
| GUI-03 | P2 | erledigt | Vorprüfung und Ergebnisse mit Scrollbars, Mindestbreiten, 500er-Seiten und Statusfiltern. Ergebnisindex erschließt alle Nachrichten und Fehler; Auswahl nutzt stabile Quellenindizes. Nachweis: GUI-Batchprüfung vom 6. September. |
| GUI-04 | P2 | erledigt | Phasen für Lesen, Cache, Export, Prüfung und Abschluss; Nachrichtenzähler, Laufzeituhr und Aktivitätsanzeige ohne falsche Gesamtprozente. Fortschritt wird zusammengefasst; Timer werden bei Abbruch/Schließen beendet. Nachweis: GUI-Batchprüfung. |
| GUI-05 | P2 | erledigt | UI-/UX-Review: konsistente deutsche Sprache und Schrittnamen, ruhigere Kopfzeile und Aktionen, eindeutiger Laufordner sowie Tastaturbedienung der Tabellen. 59 Tests, Windows-Build und vollständig bedienter synthetischer EXE-Lauf erfolgreich. [Nachweis](02_reports/2026-09-07_ui_ux_review.md). |
| GUI-06 | P2 | erledigt | Ergebnisinhalt wechselt automatisch mit der Navigation; Kernspalten sind bei Standardgröße vollständig sichtbar, Dialoge am Hauptfenster verankert und die Konfigurationsaktion bei Mindestgröße erreichbar. Mit Regressionstests, neuem Windows-Build und Computer-Use-Nachprüfung belegt. [Nachweis](02_reports/2026-09-07_ui_ux_review.md#umsetzung-und-schlussabnahme-gui-06). |
| CHECK-01 | P2 | erledigt | Größe, Änderungszeit und SHA-256 aus der Vorprüfung beim tatsächlichen Import prüfen, auch bei Cachetreffern; Berichte im Laufordner. Kein Quellsnapshot/Dateilock. [Nachweis](02_reports/2026-09-10_roadmap_foundation.md). |
| CHECK-02 | P2 | erledigt | GUI inventarisiert auch ignorierte Dateien; Zielteilbaum ausgeschlossen, Verzeichnis-Symlinks nicht rekursiv verfolgt. Ignorierte Dateien nicht auswählbar. [Nachweis](02_reports/2026-09-10_roadmap_foundation.md). |
| CHECK-03 | P2 | teilweise | Auswahlbezogene Module sowie reale Schreibziele und Platzwarnungen in GUI/CLI geprüft. Platzabschätzung heuristisch; tatsächliche Outlook-Bereitschaft und numerische Betriebsgrenzen offen. [Nachweis](02_reports/2026-09-10_roadmap_foundation.md). |
| LOG-01 | P2 | erledigt | Laufbezogenes GUI-/CLI-Protokoll und Manifest mit Start/Ende, Optionen, Quellenfortschritt und Cache-/Fehlerzählung; auch bei reinen Cacheläufen. Nachweis: Integritätsprüfung vom 6. September. |

## Import, Skalierung und fachliche Erweiterungen

| ID | Priorität | Status | Umfang / nächster Schritt |
| --- | --- | --- | --- |
| SCALE-01 | P1 | erledigt | CLI-/GUI-Nachrichtenverarbeitung und Exporte mit begrenzten Batches; synthetische EML- und Stream-Benchmarks. Quellenmetadaten und Fremdparser bleiben größenabhängig; keine feste RAM-Garantie. [Nachweis](02_reports/2026-09-06_batch_verification.md). |
| IMPORT-01 | P2 | teilweise | MSG-Datumsfehler behoben; zehn MSG-/zwölf EML-Varianten, 550 gemischte Nachrichten sowie separat komprimiertes RTF und eine echte eingebettete MSG geprüft. Eingebettete Inhalte werden sichtbar inventarisiert, aber noch nicht exportiert. Eine gültige öffentliche PST-Referenzdatei läuft über libpff mit zwei Sollnachrichten, Analysepaket und Cache. [MSG-Nachweis](02_reports/2026-09-10_synthetic_import_verification.md), [gemischter Bestand](02_reports/2026-09-10_mixed_corpus_verification.md), [PST-/RTF-/Embedded-Nachweis](02_reports/2026-09-11_libpff_pst_verification.md). Ein selbst erzeugtes synthetisches PST-Sollarchiv, Outlook und historische Archive bleiben offen. |
| IMPORT-02 | P2 | teilweise | Iteratorabschluss entfernt nur selbst hinzugefügte Stores und beendet COM auch bei Fehlern. Testdoubles prüfen vorzeitiges Schließen und vorhandene Stores. Fehler vor verfügbarer RootFolder-Referenz sowie reale Outlook-Läufe bleiben offen. Nachweis: Batchprüfung. |
| IMPORT-03 | P2 | offen | Exchange-Adressen zuverlässig auflösen und Anzeigenamen von SMTP-Adressen unterscheiden. Review P2.2. |
| EXPORT-01 | P2 | erledigt | Markdown-Metadaten sind maskiert und Mailtext steht in einem abgegrenzten Zitatbereich; XML bewahrt gültiges ergänzendes Unicode. [Nachweis](02_reports/2026-09-11_data_contract_export_hardening.md). |
| DOMAIN-01 | P3 | offen | Deduplizierung, Konversationen, Beteiligtennormalisierung und optionale Anlagenverarbeitung nach fachlicher Priorisierung. |
| AI-01 | P3 | offen | Spätere lokale Analyseumgebung und rückverfolgbare Recherche; aktuell keine direkte KI-Integration. |

## Offene Nutzerentscheidungen

Die Versionsplanung ersetzt die folgenden Entscheidungen nicht. Vorläufige
Annahme für den Dev-Pilot: EML, MSG und mindestens ein geprüfter PST-Weg. Die
Freigabekriterien der Roadmap können auch P2-/P3-Aufgaben für den Pilot erforderlich
machen; historische Prioritäten sind kein Ersatz für die konkrete Versionsabnahme.

Die Details stehen in [PROJECT_GOALS.md, offene Festlegungen](../PROJECT_GOALS.md#9-noch-offene-festlegungen).

| ID | Status | Entscheidung |
| --- | --- | --- |
| DEC-01 | teilweise | Technischer Referenzbestand 50.000 Nachrichten, Tests mit 1.000/100.000; maximale Bytegröße, Zielhardware und Laufzeitgrenzen bleiben offen. |
| DEC-02 | entschieden | Festlegung vom 11. September 2026: Der Pilot-Build muss PST ohne Outlook über einen mitgelieferten und geprüften libpff-Weg unterstützen. Paket-, Lizenz-, Offline- und EXE-Abnahme laufen unter IMPORT-01/REL-02. |
| DEC-03 | Entscheidung offen | Anlagenumfang: Inventar, Export, Volltextsuche oder weitere Verarbeitung. |
| DEC-04 | Entscheidung offen | Fachliche Abnahmefragen, erwartete Treffer und verbindliche Beleganforderungen. |
| DEC-05 | Entscheidung offen | Zielumgebung und Grenze zwischen MailAnalyst und späterer KI-Recherche. |

## Empfohlener nächster Arbeitsblock

Als nächstes den begonnenen 0.7.0-Importblock fortsetzen: ein selbst erzeugtes
synthetisches PST-Sollarchiv für mindestens ein Backend herstellen und den
Pilotumfang zu DEC-02 festlegen. Danach MSG-Sondervarianten und
Exchange-/SMTP-Auflösung (IMPORT-03)
bearbeiten. CHECK-03 hat weiter Grenzen bei Outlook-Bereitschaft und
Platzabschätzung; Referenzhardware bleibt offen. Eine neue interaktive EXE-Abnahme
für 0.7.0-dev.1 ist nachzuholen. Die [Roadmap](01_guides/ROADMAP.md) ordnet
Importabnahme, Wiederaufnahme und Umzugskriterien ein.

Die Übersicht ist kein Auftrag, alle offenen Punkte automatisch umzusetzen. Jeder neue Block erhält einen klaren Umfang und passende Abnahmekriterien.

## Ergänzende Aufgaben aus der Versionsplanung

Abnahmedetails stehen zentral in der Roadmap; Fortschritt wird hier nachgewiesen.

| ID | Priorität | Status | Umfang / geplante Version |
| --- | --- | --- | --- |
| REL-01 | P2 | teilweise | 0.5.0-dev.1 mit zentraler Version, Build-/Quellbezug, Quellsnapshot und Prüfsummen; frische Umgebung geprüft. Synthetischer EXE-Analysepaket-Workflow und Cachewiederholung bestanden; festgeschriebener Release-Quellstand und Gesamtabnahme bleiben offen. [Build](02_reports/2026-09-10_roadmap_foundation.md), [EXE-Prüfung](02_reports/2026-09-10_interactive_exe_verification.md). |
| DATA-08 | P1 | teilweise | Für den lesenden libpff-Weg blieb die gehashte öffentliche PST vor und nach frischem Import und Cachelauf bytegleich. Outlook-Erfolg, -Fehler und -Abbruch sowie eine gegebenenfalls nötige Arbeitskopie bleiben offen. [Nachweis](02_reports/2026-09-11_libpff_pst_verification.md); 0.7.0. |
| RUN-01 | P1 | offen | Checkpoints, verwaiste Läufe erkennen und sichere Wiederaufnahme an Quellengrenzen; 0.8.0. |
| RUN-02 | P1 | offen | Parserhänger und Fehler-/Abbruchgrenzen einschließlich Ressourcenfreigabe beherrschen; 0.8.0. |
| PERF-01 | P1 | offen | Referenzhardware und Zahlenlimits festlegen; synthetische Größenmatrix gegen diese Grenzen abnehmen; 0.8.0. |
| OPS-01 | P2 | offen | Bestehendes Ergebnis wieder öffnen, Fehlerhilfe und nachvollziehbare Verwaltung eigener Zwischenprodukte; bis 0.9.0-rc.1. |
| REL-02 | P1 | offen | Gesamtabnahme des konkreten EXE-Kandidaten auf sauberem Windows einschließlich Offline-Betrieb; Umzugsschwelle 0.9.0-rc.1. |
