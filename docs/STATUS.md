# MailAnalyst – aktueller Arbeitsstand

Stand: 5. September 2026. Diese Datei ist die aktuelle Übersicht; Review- und Prüfberichte dokumentieren den jeweiligen historischen Stand.

## Erreichter Stand

Der EML-Workflow wurde über CLI, Python-GUI und die gebaute Windows-EXE geprüft. Das Paket ist nach Zuständigkeiten aufgeteilt; alle eigenen Python-Dateien bleiben unter 200 Zeilen. Zuletzt bestanden zwölf automatisierte Tests. MSG-Adapter und PST-Auswahl wurden dabei mit Testdoubles geprüft, reale MSG-/PST-Archive noch nicht.

Nachweise: [Refactoring-Abnahme](02_reports/2026-09-05_refactor_verification.md), [Architektur](01_guides/ARCHITECTURE.md), [Datenmodell](01_guides/DATA_MODEL.md). Fachlicher Auftrag: [Projektziele](../PROJECT_GOALS.md).

Refactoring, nachfolgende Fehlerkorrekturen, Bereinigung und Dokumentationskonvention bilden das gemeinsam geprüfte Änderungspaket vom 5. September 2026. Alle zwölf Tests bestanden erneut vor der Git-Übergabe. Den aktuellen Commit- und Synchronisationsstand mit `git status` und `git log` feststellen. Die Windows-CI ist konfiguriert; eine erfolgreiche Ausführung auf GitHub ist noch nicht nachgewiesen.

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
| DATA-02 | P1 | offen | Pickle ersetzen; Version und Schema prüfen, beschädigte Caches kontrolliert behandeln. Review P1.3. |
| DATA-03 | P1 | offen | Hashverifikation und Cachekriterien überarbeiten; Zeitpunkt und Bedeutung eines verifizierten Quellhashes festlegen. Review P1.4. |
| DATA-04 | P1 | offen | Eindeutige Laufordner, Manifest und Status verhindern vermischte Alt-/Neuausgaben. Review P1.6. |
| DATA-05 | P1 | offen | Exporte temporär schreiben, validieren und erst dann freigeben. Review P2.7; Teil des priorisierten Integritätsblocks. |
| DATA-06 | P1 | offen | Formelinterpretation in CSV/Excel-Sichtausgaben verhindern. Masterdaten unverändert lassen. Review P1.7. |
| DATA-07 | P2 | offen | Ausführbare Schemavalidierung und Formatunterschiede absichern; DATA_MODEL beschreibt bisher nur den Iststand. |

## GUI und Prüfungen

| ID | Priorität | Status | Umfang / nächster Schritt |
| --- | --- | --- | --- |
| GUI-01 | P1 | teilweise | Feste Laufoptionen und Queue umgesetzt; Mehrfachstart-Sperren und konsistente Sperrung der Navigation fehlen. Review P1.5. |
| GUI-02 | P2 | offen | Kontrolliertes Abbrechen und Schließen bei aktiven Jobs; Daemon-Threads bleiben derzeit bestehen. Review P2.9. |
| GUI-03 | P2 | offen | Tabellenbreiten/Scrollbars korrigieren und Ergebnisvorschau für große Bestände begrenzen. |
| CHECK-01 | P2 | offen | Vorprüfung und Verarbeitung an denselben Dateistand binden. Review P2.4. |
| CHECK-02 | P2 | offen | Ignorierte Erweiterungen bei Ordnerläufen inventarisieren; aktuell vorher ausgefiltert. Review P2.5. |
| CHECK-03 | P2 | offen | Zielbezogene Schreib-/Speicherprüfung und profilabhängige Backendprüfung. Review P2.8 und Systemcheck-Review. |
| LOG-01 | P2 | teilweise | Alte Log-Handler werden geschlossen; GUI-Laufprotokoll mit Start/Ende, Optionen und Cachezählung fehlt noch. Review P2.6. |

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

Den aktuellen geprüften Stand nach Nutzerauftrag in Git sichern. Fachlich danach DATA-02 bis DATA-05 gemeinsam planen: sicheres Cacheformat, Hashkriterien, Laufordner und Manifest sowie validierte Exporte. Die GUI-Cachepfadkorrektur DATA-01 ist bereits erledigt und wird nicht erneut als offene Arbeit eingeplant.

Ein neuer Arbeitsblock soll einen klaren Umfang und passende Abnahmekriterien aus diesem Status ableiten. Die Übersicht ist kein Auftrag, alle offenen Punkte automatisch umzusetzen.
