# MailAnalyst – Datenmodell und Exportsemantik

Stand: 6. September 2026. Dieses Dokument beschreibt die aktuelle Implementierung, keine bereits durchgesetzte Schemavalidierung. Quelle sind die Module unter [parsing](../../mailanalyst/parsing), [text](../../mailanalyst/text) und [exports](../../mailanalyst/exports).

## Datensätze und fehlende Werte

Eine erfolgreich gelesene EML-/MSG-Datei erzeugt eine Nachrichtenzeile. Eine PST kann mehrere Zeilen aus Ordnern und Unterordnern erzeugen. CLI und GUI speichern den gemeinsamen Masterbestand als einzelne JSON-Nachrichtenzeilen in einer temporären SQLite-Datei. Es gibt weder eine globale eindeutige Nachrichten-ID noch eine automatische Deduplizierung.

Die Typen unten beschreiben erwartete Python-Werte. Viele fehlende Textwerte sind `""`. Nicht vorhandene Felder werden beim Export als Null ergänzt; Spalten entsprechen der Vereinigung aller Nachrichtenfelder. Besonders Fehlerzeilen aus PST-Importern enthalten nur einen Teil der Felder. Ein leerer Quellenbestand kann ohne Spalten bleiben; die Laufpakete unterstützen leere Ergebnisse einschließlich eines leeren Markdown-Index.

## Herkunft und Dateimerkmale

| Feld | Typ / Bedeutung |
| --- | --- |
| `source_path` | Text. Bei EML/MSG absoluter Quellpfad; bei einer PST-Nachricht zusammengesetzt aus Archivpfad, Ordnerpfad und interner Kennung, getrennt durch `::`. Ein solcher PST-Verweis ist kein unmittelbar öffnbarer Dateipfad. |
| `source_file_path` | Text. Absoluter Pfad der zugrunde liegenden EML-, MSG- oder PST-Datei; Bezug für Cachegruppierung. |
| `archive_path` | Text. PST-Archivpfad; bei EML/MSG leer. |
| `outlook_folder` | Text. Ordnerpfad innerhalb der PST; wird auch vom libpff-Backend verwendet. |
| `outlook_entry_id` | Text. Outlook EntryID beziehungsweise libpff-Identifier; keine formatübergreifende Identität. |
| `pst_backend` | Text, `outlook` oder `libpff` bei entsprechenden PST-Zeilen. Bei EML/MSG und manchen Fehlerfällen nicht vorhanden. |
| `file_name`, `file_ext` | Text. Name und kleingeschriebene Erweiterung der Quelldatei; bei PST auf allen Nachrichten die Archivdatei. |
| `file_size` | Ganzzahl. Größe der Quelldatei in Bytes, nicht Größe der einzelnen PST-Nachricht. |
| `modified_at` | Text. Änderungszeit der Quelldatei als ISO-Zeitstempel in UTC. |
| `modified_at_ns` | Ganzzahl. Änderungszeit aus dem Dateisystem in Nanosekunden seit Unix-Epoch; Genauigkeit hängt vom Dateisystem ab. |
| `file_sha256` | Text. SHA-256 der ganzen Quelldatei; bei PST auf Nachrichten desselben Archivs identisch. Kein Nachrichten- oder Anlagenhash. |
| `cache_schema_version` | Ganzzahl, derzeit `6`. Interne Cachekompatibilität; keine allgemeine Export- oder Anwendungsversion. |

`message_id`, Pfad und Hash erfüllen verschiedene Zwecke. Keines dieser Felder allein garantiert eine eindeutige, dauerhaft unveränderliche Nachrichtenidentität.

## Nachrichtenkopf und Beteiligte

| Feld | Bedeutung |
| --- | --- |
| `message_id` | Internet-Message-ID, soweit vom jeweiligen Importer verfügbar. Kann fehlen oder in mehreren Quellen wiederkehren. |
| `in_reply_to`, `references` | Antwortbezug und Referenzheader als Text. EML und MSG lesen sie, PST-Importer lassen sie derzeit leer. Keine berechnete Konversationsstruktur. |
| `subject` | Betreff als Text. |
| `from_name`, `from_email` | Absendername und Adresse, soweit extrahierbar. Exchange-interne Werte sind nicht zuverlässig auf SMTP normalisiert. |
| `to`, `cc`, `bcc`, `reply_to` | Empfänger-/Antwortadressen als Darstellungszeichenfolge. Bei EML typischerweise `Name <adresse>`; Einträge durch `; ` getrennt. Andere Formate können rohe Anzeigenamen liefern. |
| `to_emails`, `cc_emails`, `bcc_emails`, `reply_to_emails` | Extrahierte Adressen als Zeichenfolge, nicht als Liste. Bei PST nicht durchgehend reine SMTP-Adressen. |

MSG und beide PST-Importer lassen `reply_to` und `reply_to_emails` derzeit leer. libpff übernimmt `display_to`, `display_cc` und `display_bcc` auch in die jeweiligen `_emails`-Felder. Es gibt keine zuverlässige Erkennung von Versand-/Empfangsrichtung relativ zu einem Postfach.

## Datum und Zeitzonen

`sent_at` enthält bei erfolgreicher Interpretation einen ISO-Zeitstempel mit ursprünglichem beziehungsweise angenommenem Offset. Bei ungültigem Datum kann der unverarbeitete Datumswert erhalten bleiben. `sent_at_utc` enthält die UTC-Normalisierung oder einen leeren Text bei fehlgeschlagener Interpretation.

Aktuelle Unterschiede:

- EML und textuelle MSG-Datumswerte verwenden den gemeinsamen Datumsparser. MSG übernimmt `datetime`-Werte der Bibliothek direkt und normalisiert sie auf UTC. Werte ohne Zeitzone werden bei beiden Wegen als UTC interpretiert. Fehlende MSG-Daten bleiben leer. Reale synthetische MSG-Dateien sichern Monatswechsel und beide Zeitumstellungen ab.
- Outlook-PST interpretiert naive `datetime`-Werte als die gewählte Zeitzone, standardmäßig `Europe/Berlin`.
- libpff-PST interpretiert naive `datetime`-Werte als UTC. Als Datumsquelle wird `client_submit_time`, ersatzweise bei fehlgeschlagenem Attributzugriff `delivery_time`, herangezogen.
- Eine gleichwertige Normalisierung aller Importformate ist deshalb noch nicht garantiert.

Die folgenden Felder werden aus `sent_at_utc` in der gewählten Zeitzone abgeleitet. Bei fehlendem/ungültigem UTC-Wert oder unbekannter Zielzeitzone bleiben sie leer; die numerischen Felder können dann Text/Ganzzahl-Mischungen enthalten.

| Feld | Darstellung |
| --- | --- |
| `sent_date_de` | `TT.MM.JJJJ` |
| `sent_time_de` | `HH:MM:SS` |
| `sent_datetime_de` | `TT.MM.JJJJ HH:MM:SS` |
| `sent_year`, `sent_month` | Kalenderjahr und Monat als Ganzzahl |
| `sent_month_name_de` | Deutscher Monatsname; März wird aktuell `Maerz` geschrieben |
| `sent_year_month` | `JJJJ-MM` in der gewählten Zeitzone |
| `sent_quarter` | `Q1` bis `Q4` |
| `sent_calendar_week`, `sent_iso_year` | ISO-Kalenderwoche und zugehöriges ISO-Jahr |
| `sent_weekday_de` | Deutscher Wochentag |

Wichtig für Monatsdateien: Markdown partitioniert nach dem **UTC-Monat** aus `sent_at_utc`, nicht nach `sent_year_month`. Eine Mail vom 31. August, 23:30 UTC, liegt im August-Chunk, obwohl ihre Berliner Anzeige bereits den 1. September zeigt. Die aktuellen Tests enthalten genau diesen Grenzfall.

## Text und Anlagen

| Feld | Bedeutung |
| --- | --- |
| `body_text_raw` | Extrahierter Plaintext nach MIME-/Bibliotheksdekodierung; kein bytegetreues Original. Bei reinen HTML-Nachrichten kann er leer sein. |
| `body_text_clean` | Bereinigter Suchtext. Falls nötig aus HTML abgeleitet; die genaue Auswahl unterscheidet sich nach Importer. |
| `body_text` | Gleicher Inhalt wie `body_text_clean`. |
| `body_preview` | Erste 500 Zeichen des bereinigten Texts, kein inhaltliches Resümee. |
| `body_html` | Extrahierter HTML-Inhalt als Text, soweit vorhanden. |
| `body_text_length`, `body_text_raw_length`, `body_html_length` | Python-Zeichenanzahl der jeweiligen Textvariante, keine Bytezahl. |
| `has_attachments` | Boolean aus dem erkannten Anlageninventar. |
| `attachment_count` | Ganzzahl, Anzahl erkannter Anlagen. |
| `attachment_names` | Mit `; ` verbundene Namen; kein strukturiertes Anlagenmodell. Fehlende Namen können je nach Importer ausgelassen werden. |
| `mime_defects` | Bei EML erkannte Parserdefektnamen als Zeichenfolge; bei anderen Formaten derzeit leer. |

EML inventarisiert Teile mit Disposition `attachment`; Inline-Inhalte müssen daher nicht als Anlagen zählen. Anlagen werden weder exportiert noch gehasht. Unterschiedliche Zählweisen der Importbibliotheken sind zu berücksichtigen. `has_attachments = false` beweist nicht, dass die Originalnachricht keine eingebetteten Inhalte besitzt.

## Fehlersemantik

`parse_status` ist derzeit `ok` oder `error`. `parse_error` enthält bei einem abgefangenen Parserfehler dessen Text. `ok` bedeutet, dass der Parseraufruf ohne abgefangene Ausnahme eine Zeile lieferte; es bestätigt keine Vollständigkeit, fachliche Richtigkeit oder Fehlerfreiheit des Quellformats.

Der Dispatcher erzeugt bei abgefangenen Quellenfehlern eine Zeile mit Herkunftsbezug und leeren Nachrichtenfeldern. Fehler bei Dateisuche, Dateisignatur, vorgezogener Hashberechnung, Cachezugriff oder Export können dagegen den gesamten Lauf abbrechen. PST-interne Fehlerzeilen enthalten teilweise nur Herkunft, Kennung, Betreff und Fehlerstatus. Manche PST-Eigenschaftsfehler werden vom Importer abgefangen und durch leere Werte ersetzt.

Vorprüfungsstatus (`ok`, `warning`, `error`, `ignored`) sind davon getrennt und stehen in den Vorprüfungsberichten. Sie sind keine Werte von `parse_status`.

Vorprüfungszeilen enthalten zusätzlich `sha256` für lesbare unterstützte Dateien.
Ignorierte oder nicht prüfbare Dateien haben keinen verwendbaren Fingerabdruck.
Größe, Nanosekunden-Änderungszeit und Hash werden für ausgewählte Dateien direkt
vor dem Lesen gegen den Vorprüfungsstand geprüft. Fehler während dieser Bindung
brechen den Lauf ab. Vorprüfungsergebnisse sind Fingerabdrücke, keine Quellkopien.

## Cache und Nachweisgrenzen

Der primäre interne Cache ist SQLite mit getrennten Tabellen für Quellenkriterien/Audits und einzelne JSON-Nachrichten (Speicherformatversion 2). Speicherformat 1 wird beim ersten CLI-/GUI-Lauf neu aufgebaut. JSON-Einträge werden auf Struktur, skalare Nachrichtendaten und Übereinstimmung mit Quellkriterien geprüft. `cache_schema_version` in den Exportzeilen bleibt 6; die getrennte Parserrevision ist seit der MSG-Datumskorrektur vom 10. September 2026 auf 2 erhöht. Ältere Parserrevisionen werden neu importiert, damit zuvor verlorene MSG-Versanddaten wiederhergestellt werden. Die Validierung ist keine vollständige fachliche Schemavalidierung aller Nachrichtenfelder (DATA-07).

GUI: `<Zielordner>/.mailanalyst_cache/mail_metadata.sqlite3`; CLI: relativ zum Arbeitsordner oder explizit über `--cache`. Bei `.pkl`-/`.pickle`-Pfaden wird eine gleichnamige `.sqlite3`-Datei verwendet. Alte Pickles werden weder geladen noch verändert. Beschädigte beziehungsweise inkompatible Caches werden mit Warnung neu aufgebaut. Eine neue Cachedatei ersetzt die alte erst nach erfolgreichem Abschluss der Quellverarbeitung. Fehlerhafte Quellen werden nicht als Cachetreffer wiederverwendet; leere erfolgreich gelesene Archive können gespeichert werden. Der Cache enthält weiterhin die Quellen des letzten Laufs, keine dauerhafte Archivdatenbank.

Cachekriterien sind Quellpfad, Größe, Änderungszeit, Schema-/Parserrevision, Zielzeitzone und tatsächlich gewähltes PST-Backend (auch bei `auto`). Mit `--hash-check` muss zusätzlich der aktuelle SHA-256 übereinstimmen. Neue Importe werden vor und nach dem Parsen vollständig gehasht; strenge Cachetreffer ebenfalls vor und nach der Übernahme. Unterschiedliche Signaturen brechen den Lauf ab, ohne den bisherigen Cache zu ersetzen.

GUI-/CLI-Läufe verwenden unabhängig von der kompatiblen `hash_check`-Option die
Pflichtbindung `preflight_binding=sha256` und dadurch stets aktuell geprüfte
Cachetreffer. Der schnelle ungeprüfte Modus bleibt nur für direkte Kernaufrufe
ohne Vorprüfungsbindung verfügbar. Die GUI kopiert die Auswahl samt Fingerabdrücken
in den Auftrag; direkte Service-Aufrufe ohne übergebene Vorprüfung und die CLI
prüfen zunächst die ausgewählten Dateien neu.

Das Manifest verweist über `sources_file` auf `sources.jsonl`. Diese Datei enthält pro Quelle Hash, Größe, Änderungszeit, Backend, Nachrichten-/Fehlerzahl und `mode` (`parsed`/`cache`). `hash_status=verified_this_run` und `hash_verified_at` bezeichnen die aktuelle Prüfung. Bei schnellen Cachetreffern steht `reused_unverified` mit leerem Verifikationszeitpunkt; `file_sha256` bleibt der frühere Hash. Die Nachrichtenexporte erhalten keine zusätzlichen Auditspalten.

Diese Vorher-/Nachher-Prüfung ist keine Dateisperre oder unveränderliche Quellkopie. Kurzzeitige Änderungen mit vollständiger Wiederherstellung sowie Änderungen nach der Prüfung sind nicht ausgeschlossen. Für PST gilt der Hash dem gesamten Archiv. Outlook-bedingte Archivänderungen können deshalb einen Lauf ablehnen; echte PST-Workflows sind weiterhin praktisch zu prüfen.

## Laufpakete und Veröffentlichung

GUI und CLI erzeugen `<Zielbereich>/runs/<UTC-Zeit>-<UUID>/`. `manifest.json` (Version 2 für CLI/GUI) enthält Optionen, Versionen, den Verweis auf die Quellenprüfung, Zähler, Batchkennzahlen, UTC-Start/Ende sowie relative Exportpfade mit Größe und SHA-256. Status: `running`, `completed`, `completed_with_errors` (Parserfehlerzeilen), `cancelled` (kooperativer GUI-Abbruch vor Veröffentlichung) oder `failed`. Nach Prozessabbruch verbleibendes `running` bedeutet unvollständig; es gibt keine automatische Wiederaufnahme.

Ausgaben entstehen unter `.pending/`. Strukturierte Einzelexporte werden zurückgelesen und auf Nachrichtenanzahl geprüft; Markdown-Einzeldateien auf Kopf/Anzahl, Monatsindizes auf Anzahl, sichere relative Dateipfade und vorhandene Anker. Erst danach wird das Paketverzeichnis nach `exports/` umbenannt und der Abschluss im Manifest gespeichert. Das Manifest ist das maßgebliche Abschlusssignal. Logs, GUI-Optionen und eine Kopie der Vorprüfung sowie auftragsbezogene Systemberichte liegen im Laufordner. Die ursprünglichen GUI-Berichte im Zielbereich bleiben vorläufig. Die laufbezogene Vorprüfung beschreibt die tatsächliche Auswahl, ist aber keine unveränderliche Kopie der Originaldateien.

Das additive Manifestfeld `application` nennt die zentrale App-Version und den
Buildstatus. Gebaute EXEs ergänzen Buildzeit, Python-/Paketversionen, Quellrevision,
Änderungsstatus und Quellbaum-Hash aus der eingebetteten `build_info.json`.
Entwicklungsaufrufe melden `development`; sie behaupten keine festgeschriebene
Quellrevision. App-Versionen sind unabhängig von Cache- und Parserrevisionen.

Die GUI prüft Abbruchanforderungen bei Quellen-/Hasharbeit, vor dem Cacheersatz und zwischen Exporten. Nachrichten-/Exportschleifen und Validierung prüfen das Signal ebenfalls; laufende Parser-/Bibliotheksaufrufe werden nicht gewaltsam unterbrochen. Vor der Paketveröffentlichung entscheidet eine synchronisierte Grenze: Eine bereits angeforderte Stornierung gewinnt und erzeugt `cancelled`; eine danach eingehende Anforderung wartet auf den regulären Abschluss. Der Cache kann bereits vor einem späteren Exportabbruch erfolgreich aktualisiert worden sein. Er ist unabhängig vom Abschlussstatus des Laufpakets wiederverwendbar.

Explizite CLI-Ausgabepfade bleiben zusätzliche Kompatibilitätskopien nach Paketvalidierung. Einzeldateien werden per temporärer Datei ersetzt; vorhandene Markdown-Verzeichnisse werden unter `.previous-<UUID>` im selben Elternordner erhalten und durch eine neue Kopie ersetzt. Mehrere solche Zielpfade bilden keine gemeinsame atomare Transaktion. Bei Fehlern ist das Manifest maßgeblich; frühere Laufpakete bleiben unverändert. Es wird keine Stromausfall-Dauerhaftigkeit oder manipulationssichere Signatur zugesichert.

## Ausgabeformate und abgeleitete Ansichten

| Ausgabe | Aktuelles Verhalten |
| --- | --- |
| Parquet | Alle Spalten in begrenzten Rowgroups. Ein global ermitteltes Schema bleibt über alle Batches gleich: reine Ganzzahlen → int64, Boolean → bool, Zahlmischungen → float64, übrige Spalten → Text. Gemischte Ganzzahl/Leertext-Datumsfelder werden als Text gespeichert; Null bleibt Null. |
| JSON | Inkrementelles Array von Records, Unicode und skalare Python-Typen erhalten, fehlende Felder `null`. |
| CSV | Alle übergebenen Spalten, UTF-8 mit BOM; Typinformationen gehen verloren. Formelverdächtige Zeichenfolgen erhalten ein führendes Apostroph ausschließlich in dieser Sichtausgabe. |
| Excel | Streaming im Write-only-Modus; mehr als 1.048.575 Nachrichten werden mit Hinweis auf JSON/Parquet abgelehnt. Alle übergebenen Spalten; Zeichenfolgen werden auf 32.767 Zeichen gekürzt und ausdrücklich als Textzellen gespeichert, ohne Formeln oder automatische Hyperlinks. CR kann beim XLSX-Rücklesen als LF erscheinen. Sichtformat, kein verlustfreies Masterformat. |
| XML | Wurzel `emails` mit `count`, darunter `email` und Elemente je Spalte; Werte als Text, fehlende Werte leer. Die aktuelle Filterung entfernt auch Zeichen außerhalb der BMP. |
| Markdown | Lesbare Auswahl von Metadaten und bereinigtem Text, keine vollständige oder verlustfreie Repräsentation. |

Der CSV-Schutz gilt auch für CSV-Monatsindizes, Vorprüfungs- und Systemberichte. Zeichenfolgen mit `=`, `+`, `-`, `@` oder deren Vollbreitenvarianten nach führenden Leer-/Steuerzeichen beziehungsweise BOM werden mit `'` präfixiert; ebenso Texte mit führendem Tab, CR oder LF. Numerische Werte (einschließlich negativer Zahlen) bleiben unverändert. JSON-/JSONL-/Parquet-Ausgaben und Cache-/Masterdaten erhalten keine Schutzpräfixe. Der CSV-Index ist daher eine Sichtdarstellung; für unveränderte Metadaten dient `index.jsonl`.

Die reduzierte Listenansicht benennt ausgewählte Spalten auf Deutsch um und verwendet `body_preview` statt vollständigem Text. Die aktuelle Zuordnung steht in [list_export_dataframe](../../mailanalyst/exports/tabular.py). Sie ist von einem vollständigen CSV-/Excel-Masterexport zu unterscheiden.

Die Markdown-Linkmodi `full`, `compact` und `text_only` betreffen nur die Markdown-Bodydarstellung. Sie verändern weder Parquet/JSON noch automatisch alle Indexfelder. Beispielsweise bleibt `body_preview` im Index unverändert und kann weiterhin URLs enthalten.

Der Monatsindex (`index.csv` und `index.jsonl`) enthält `chunk`, `markdown_file`, `anchor`, `sent_at_utc`, `sent_datetime_de`, `from_email`, `to_emails`, `cc_emails`, `subject`, `message_id`, `attachment_names`, `source_path` und `body_preview`. `markdown_file` ist relativ zum Markdown-Ausgabeordner und verwendet portable `/`-Pfadtrenner. `anchor` ist eine laufende Nummer innerhalb eines Monats und kann sich bei neuen Läufen ändern. Unbekannte Datumswerte werden unter `unbekannt` gruppiert.

## Batchverarbeitung und Grenzen

Standard sind 500 Nachrichten pro Batch; die CLI erlaubt `--batch-size 1..5000`. Zusätzlich beendet ein Textvolumen von etwa 8 MiB einen Batch. Eine einzelne größere Nachricht kann diese Schwelle überschreiten. EML/MSG werden mit höchstens zweimal der Workerzahl gleichzeitig eingeplanten Quellen gelesen; PST-Iteratoren liefern einzelne Nachrichten und werden bei Abbruch geschlossen. Bereits gelesene PST-Nachrichten bleiben bei einem späteren abgefangenen Quellenfehler zusammen mit einer Fehlerzeile erhalten; die Quelle wird nicht als Cachetreffer wiederverwendet.

JSON, CSV, XML und Excel werden zeilenweise geschrieben, Parquet in Rowgroups. Markdown-Monate werden über SQLite sortiert und direkt mit ihren Indizes geschrieben. Die Validierung liest die Formate inkrementell zurück; Markdown-Einzelexporte werden nur anhand ihres Kopfes geprüft. `work.sqlite3` ist das interne Arbeitsartefakt im Laufordner; nach einem regulären Service-/CLI-Abschluss wird es geschlossen und entfernt. Nach frühem Fehler oder Prozessabbruch kann es zur Diagnose zurückbleiben, ohne Wiederaufnahmefunktion.

Der GUI-Service liefert nur eine Vorschau von höchstens 500 Nachrichten und etwa 8 MiB serialisierten Quelldaten, gegebenenfalls zuzüglich einer großen Einzelzeile. `total_messages`, `total_errors` und `run_directory` stehen in DataFrame-Attributen. Die vollständigen Daten liegen in den Exporten. GUI-Läufe enthalten zusätzlich `exports/review.sqlite3` mit einer Tabelle `review` (`seq`, `status`, `payload`) und einem Statusindex. Das JSON-Payload enthält als Text `sent_datetime_de`, `from_email`, `subject`, `file_ext`, `parse_status`, `parse_error` und `source_path`; fehlende Werte erscheinen leer. Es enthält keine Mailtexte, aber vertrauliche Metadaten und vollständige Fehler-/Herkunftsbezüge. Die laufende `seq` gilt nur innerhalb dieses Laufs, nicht als dauerhafte Nachrichten-ID. Der Index gehört zu den gehashten Exportdateien. Seiten und Fehlerfilter lesen jeweils höchstens 500 Einträge; ein fehlender Index erlaubt nur die bereits übergebene Vorschau. Quellpfadlisten, Vorprüfungsdaten, Ordnerrekursion sowie der Speicher einer einzelnen Nachricht beziehungsweise Importbibliothek sind weiterhin größenabhängig; dies ist keine feste Gesamt-RAM-Garantie.

`pipeline.build_dataframe`, die Listen-Parserhelfer und DataFrame-Exporter bleiben als materialisierende Kompatibilität für kleine direkte Python-Aufrufe erhalten. Sie sind nicht der skalierbare CLI-/GUI-Pfad und verwenden weiterhin die bisherige DataFrame-Typableitung beziehungsweise Cacheversion 1.

## Änderungen an diesem Modell

Änderungen an Feldnamen, Bedeutung, Datumsannahmen oder Exportverlusten benötigen passende Regressionstests und eine Aktualisierung dieses Dokuments sowie der betroffenen Bedienhinweise. Neue verbindliche Schemas, Nachrichten-IDs und Migrationsregeln sind noch zu entwickeln; dieses Dokument führt sie nicht stillschweigend ein.
