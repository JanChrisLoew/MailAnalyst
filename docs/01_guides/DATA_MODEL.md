# MailAnalyst – Datenmodell und Exportsemantik

Stand: 5. September 2026. Dieses Dokument beschreibt die aktuelle Implementierung, keine bereits durchgesetzte Schemavalidierung. Quelle sind die Module unter [parsing](../../mailanalyst/parsing), [text](../../mailanalyst/text) und [exports](../../mailanalyst/exports).

## Datensätze und fehlende Werte

Eine erfolgreich gelesene EML-/MSG-Datei erzeugt eine Nachrichtenzeile. Eine PST kann mehrere Zeilen aus Ordnern und Unterordnern erzeugen. Der gemeinsame Masterbestand ist ein Pandas-DataFrame aus den zurückgegebenen Dictionaries. Es gibt weder eine globale eindeutige Nachrichten-ID noch eine automatische Deduplizierung.

Die Typen unten beschreiben erwartete Python-Werte vor der Zusammenführung. Viele fehlende Textwerte sind `""`. Fehlende Felder einzelner Dictionaries können im DataFrame zu `NaN`/Null und geänderten Spaltentypen führen. Besonders Fehlerzeilen aus PST-Importern enthalten nur einen Teil der Felder. Ein leerer Quellenbestand kann einen DataFrame ohne Spalten erzeugen; nicht alle nachgelagerten Exporte behandeln diesen Fall zuverlässig.

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

- EML und MSG verwenden den gemeinsamen Datumsparser. Werte ohne Zeitzone werden dort als UTC interpretiert. MSG übergibt den Bibliothekswert als Text; nicht jede mögliche Darstellung ist damit zuverlässig abgedeckt.
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

## Cache und Nachweisgrenzen

Der Cache enthält den gesamten Master-DataFrame als Pickle. GUI: unter dem gewählten Zielordner; CLI: Standardpfad relativ zum Arbeitsordner oder explizit über `--cache`.

Cachetreffer prüfen derzeit Schema-Version, Dateigröße und Änderungszeit. Optional wird der Quellhash verglichen; bei expliziter PST-Backendwahl außerdem das Backend. Eine andere Zielzeitzone ist bisher kein Invalidierungskriterium. Daher bei geänderter Datumsinterpretation aktuell neu parsen (`--refresh`).

Ohne strenge Hashprüfung kann `file_sha256` bei Cachetreffern aus einem früheren Lauf stammen. Es gibt kein Feld für den Verifikationszeitpunkt und kein Laufmanifest. Das Modell liefert Herkunftshinweise, aber keinen automatisch gesicherten Beweis für unveränderte Quellen. Offene Arbeiten: [DATA-02 bis DATA-05](../STATUS.md#integrität-und-laufstruktur).

## Ausgabeformate und abgeleitete Ansichten

| Ausgabe | Aktuelles Verhalten |
| --- | --- |
| Parquet | Vollständige DataFrame-Spalten mit von Pandas/PyArrow abgeleiteten Typen. |
| JSON | Array von Records, Unicode erhalten, fehlende DataFrame-Werte können `null` werden. |
| CSV | Alle übergebenen Spalten, UTF-8 mit BOM; Typinformationen gehen verloren. Kein aktueller Schutz gegen Formelinterpretation. |
| Excel | Alle übergebenen Spalten; Zeichenfolgen werden auf 32.767 Zeichen gekürzt. Sichtformat, kein verlustfreies Masterformat. |
| XML | Wurzel `emails` mit `count`, darunter `email` und Elemente je Spalte; Werte als Text, fehlende Werte leer. Die aktuelle Filterung entfernt auch Zeichen außerhalb der BMP. |
| Markdown | Lesbare Auswahl von Metadaten und bereinigtem Text, keine vollständige oder verlustfreie Repräsentation. |

Die reduzierte Listenansicht benennt ausgewählte Spalten auf Deutsch um und verwendet `body_preview` statt vollständigem Text. Die aktuelle Zuordnung steht in [list_export_dataframe](../../mailanalyst/exports/tabular.py). Sie ist von einem vollständigen CSV-/Excel-Masterexport zu unterscheiden.

Die Markdown-Linkmodi `full`, `compact` und `text_only` betreffen nur die Markdown-Bodydarstellung. Sie verändern weder Parquet/JSON noch automatisch alle Indexfelder. Beispielsweise bleibt `body_preview` im Index unverändert und kann weiterhin URLs enthalten.

Der Monatsindex (`index.csv` und `index.jsonl`) enthält `chunk`, `markdown_file`, `anchor`, `sent_at_utc`, `sent_datetime_de`, `from_email`, `to_emails`, `cc_emails`, `subject`, `message_id`, `attachment_names`, `source_path` und `body_preview`. `markdown_file` ist relativ zum Markdown-Ausgabeordner und verwendet derzeit plattformabhängige Pfadtrenner. `anchor` ist eine laufende Nummer innerhalb eines Monats und kann sich bei neuen Läufen ändern. Unbekannte Datumswerte werden unter `unbekannt` gruppiert.

## Änderungen an diesem Modell

Änderungen an Feldnamen, Bedeutung, Datumsannahmen oder Exportverlusten benötigen passende Regressionstests und eine Aktualisierung dieses Dokuments sowie der betroffenen Bedienhinweise. Neue verbindliche Schemas, Nachrichten-IDs und Migrationsregeln sind noch zu entwickeln; dieses Dokument führt sie nicht stillschweigend ein.
