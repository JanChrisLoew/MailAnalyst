# MailAnalyst – aktueller Arbeitsstand

Stand: 6. September 2026. Diese Datei ist die aktuelle Übersicht; Review- und Prüfberichte dokumentieren den jeweiligen historischen Stand.

## Erreichter Stand

Der Integritätsblock und der anschließende GUI-/Exportblock vom 6. September sind umgesetzt. Neben SQLite-Cache und Laufpaketen gibt es eine zentrale GUI-Startsperre, kooperativen Abbruch, geordnetes Schließen und Schutz gegen Formelinterpretation in CSV-/Excel-Sichtausgaben. 39 automatisierte Tests bestanden einschließlich CLI und Python-GUI; der Windows-Build war erfolgreich. Für diesen Stand fehlt eine vollständige Bedienprüfung der gebauten EXE. MSG-/PST-Adapter wurden weiterhin nur mit Testdoubles geprüft, reale Archive noch nicht.

Nachweise: [GUI-/Exportprüfung](02_reports/2026-09-06_gui_export_safety.md), [Integritätsprüfung](02_reports/2026-09-06_integrity_verification.md). Die [Refactoring-Abnahme vom 5. September](02_reports/2026-09-05_refactor_verification.md) dokumentiert den zuvor vollständig geprüften EML-EXE-Workflow. Alle eigenen Python-Dateien bleiben unter 200 Zeilen. Fachlicher Auftrag: [Projektziele](../PROJECT_GOALS.md).

Integritätsblock und GUI-/Exportblock bilden das gemeinsam geprüfte Änderungspaket für die Git-Übergabe vom 6. September. Den aktuellen Commit- und Synchronisationsstand mit `git status` und `git log` feststellen. Die Windows-CI ist konfiguriert; eine erfolgreiche Ausführung auf GitHub ist noch nicht nachgewiesen.

## Prioritäten und Statusregeln

P1: vor einem Pilot mit großen Archiven. P2: vor breiter Verteilung beziehungsweise für zuverlässige Weiterentwicklung. P3: spätere fachliche Erweiterung oder noch zu priorisierende Infrastruktur.

Statuswerte: **erledigt**, **teilweise**, **offen**, **Entscheidung offen**. „Erledigt“ bezieht sich jeweils nur auf den beschriebenen Umfang. IDs bleiben erhalten; beim Abschluss Nachweis und Datum ergänzen. Neue Aufgaben bekommen neue IDs. Detaillierte Gründe stehen im [Review vom 4. September](02_reports/2026-09-04_review_report.md).

## Struktur, Tests und Dokumentation

| ID | Priorität | Status | Umfang / nächster Schritt |
| --- | --- | --- | --- |
| REPO-01 | P2 | erledigt | Modularisierung und 200-Zeilen-Prüfung; siehe Refactoring-Abnahme vom 5. September. |
| REPO-02 | P2 | teilweise | Lokale Tests und CI-Konfiguration vorhanden; ersten erfolgreichen GitHub-Lauf noch nachweisen. |
| REPO-03 | P2 | erledigt | Agent-Einstieg, aktueller Status, Datenmodell und Repository-Prüfskill angelegt; Dokumentationsverweise geprüft. Am 5. September 2026 die verbindliche [Dokumentationsprüfung nach Änderungen](01_guides/ARCHITECTURE.md#dokumentationsprüfung-nach-änderungen) ergänzt und über AGENTS.md eingebunden. |
| REPO-04 | P3 | offen | Reproduzierbare Abhängigkeiten und zentrale Toolkonfiguration bewerten; bislang Mindestversionen in requirements-Dateien. |
| REPO-05 | P3 | offen | Einheitliche Formatierung und automatisierte Dokumentations-Linkprüfung in CI ergänzen. |
| REPO-06 | P2 | erledigt | Bereinigung am 5. September 2026: alte Prüf-Kompatibilitätsmodule und CLI-Funktions-Reexports entfernt; Tests importieren direkt aus dem Paket. Berichte nach `docs/02_reports/` verschoben, README und Prüfskill aktualisiert, drei temporäre Prüfverzeichnisse entfernt. Zwölf Tests einschließlich CLI und Python-GUI bestanden; Skill validiert. Keine erneute EXE-Abnahme, da deren Paketimporte und Ressourcen unverändert sind. |

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
| DATA-07 | P2 | offen | Ausführbare Schemavalidierung und Formatunterschiede absichern; DATA_MODEL beschreibt bisher nur den Iststand. |

## GUI und Prüfungen

| ID | Priorität | Status | Umfang / nächster Schritt |
| --- | --- | --- | --- |
| GUI-01 | P1 | erledigt | Zentrale Einzeljobsperre, gesperrte Navigation/Eingaben und Startguards; frühere Ergebnisse bei neuen Läufen gesperrt. Doppeltstart und Neustart im Tk-Test geprüft. Nachweis: GUI-/Exportprüfung vom 6. September. |
| GUI-02 | P2 | erledigt | Kooperativer Abbruch, nicht als Daemon gestarteter Worker und Warten beim Schließen; keine erzwungene Unterbrechung von Bibliotheksaufrufen. Abbruch-/Veröffentlichungsgrenze synchronisiert. Nachweis: GUI-/Exportprüfung vom 6. September. |
| GUI-03 | P2 | offen | Tabellenbreiten/Scrollbars korrigieren und Ergebnisvorschau für große Bestände begrenzen. |
| CHECK-01 | P2 | offen | Vorprüfung und Verarbeitung an denselben Dateistand binden. Review P2.4. |
| CHECK-02 | P2 | offen | Ignorierte Erweiterungen bei Ordnerläufen inventarisieren; aktuell vorher ausgefiltert. Review P2.5. |
| CHECK-03 | P2 | offen | Zielbezogene Schreib-/Speicherprüfung und profilabhängige Backendprüfung. Review P2.8 und Systemcheck-Review. |
| LOG-01 | P2 | erledigt | Laufbezogenes GUI-/CLI-Protokoll und Manifest mit Start/Ende, Optionen, Quellenfortschritt und Cache-/Fehlerzählung; auch bei reinen Cacheläufen. Nachweis: Integritätsprüfung vom 6. September. |

## Import, Skalierung und fachliche Erweiterungen

| ID | Priorität | Status | Umfang / nächster Schritt |
| --- | --- | --- | --- |
| SCALE-01 | P1 | offen | Stapelweise Verarbeitung und inkrementelle Exporte statt vollständigem Datenbestand im RAM. Review P1.1. |
| IMPORT-01 | P2 | offen | Repräsentative MSG-/PST-Testarchive und beide PST-Wege praktisch verifizieren. Testdoubles reichen dafür nicht. Review P2.3. |
| IMPORT-02 | P2 | offen | Outlook-Store-Lifecycle und Cleanup bei frühen Fehlern härten. Review P2.1. |
| IMPORT-03 | P2 | offen | Exchange-Adressen zuverlässig auflösen und Anzeigenamen von SMTP-Adressen unterscheiden. Review P2.2. |
| EXPORT-01 | P2 | offen | Markdown-Metadaten maskieren, Mailinhalt und generierte Struktur robuster trennen. Review P2.10. |
| DOMAIN-01 | P3 | offen | Deduplizierung, Konversationen, Beteiligtennormalisierung und optionale Anlagenverarbeitung nach fachlicher Priorisierung. |
| AI-01 | P3 | offen | Spätere lokale Analyseumgebung und rückverfolgbare Recherche; aktuell keine direkte KI-Integration. |

## Offene Nutzerentscheidungen

Die Details stehen in [PROJECT_GOALS.md, offene Festlegungen](../PROJECT_GOALS.md#9-noch-offene-festlegungen).

| ID | Status | Entscheidung |
| --- | --- | --- |
| DEC-01 | Entscheidung offen | Typische/maximale Archivgröße, Nachrichtenanzahl, Zielhardware und Laufzeitgrenzen. |
| DEC-02 | Entscheidung offen | Muss der erste verteilte Build PST zwingend ohne Outlook unterstützen? |
| DEC-03 | Entscheidung offen | Anlagenumfang: Inventar, Export, Volltextsuche oder weitere Verarbeitung. |
| DEC-04 | Entscheidung offen | Fachliche Abnahmefragen, erwartete Treffer und verbindliche Beleganforderungen. |
| DEC-05 | Entscheidung offen | Zielumgebung und Grenze zwischen MailAnalyst und späterer KI-Recherche. |

## Empfohlener nächster Arbeitsblock

Als nächstes repräsentative MSG-/PST-Importwege praktisch abnehmen und den Großmengenblock vorbereiten. Dafür Archivgröße/Zielhardware und den Umfang des Outlook-unabhängigen PST-Pakets klären. Parallel fachlich festlegen, welche synthetischen Recherchefragen und erwarteten Treffer die Pilotabnahme belegen sollen. Die vollständige EXE-Bedienprüfung des aktuellen Stands sowie der erste erfolgreiche GitHub-CI-Lauf bleiben nachzuweisen.

Die Übersicht ist kein Auftrag, alle offenen Punkte automatisch umzusetzen. Jeder neue Block erhält einen klaren Umfang und passende Abnahmekriterien.
