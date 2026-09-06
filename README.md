# MailAnalyst

Ein lokales Python-Werkzeug, um Outlook-E-Mails aus `.eml`, `.msg` und `.pst` auszulesen und strukturiert bereitzustellen. Neben der Kommandozeile gibt es eine minimalistische Desktop-Oberflaeche.

## Dokumentation

| Einstieg | Inhalt |
| --- | --- |
| [Projektziele](PROJECT_GOALS.md) | Fachlicher Nutzen, Umfang und offene Nutzerentscheidungen |
| [Aktueller Status](docs/STATUS.md) | Erledigtes, offene Aufgaben mit IDs und nächste Prioritäten |
| [Architektur](docs/01_guides/ARCHITECTURE.md) | Modulstruktur und gemeinsame Entwicklungsregeln |
| [Datenmodell](docs/01_guides/DATA_MODEL.md) | Felder, Herkunft, Datumsannahmen und Exportsemantik |
| [Agent-Einstieg](AGENTS.md) | Kontextauswahl und Hinweise für Coding Agents |
| [Prüfskill](.agents/skills/mailanalyst-verify/SKILL.md) | Wiederholbarer Ablauf für vollständige App- und EXE-Abnahmen |
| [Historischer Review](docs/02_reports/2026-09-04_review_report.md) / [Refactoring-Abnahme](docs/02_reports/2026-09-05_refactor_verification.md) | Befunde und Nachweise des jeweiligen Prüfzeitpunkts |

## Dateien im Projekt

Das Projekt trennt Einstiegspunkte, Anwendungslogik, Oberfläche und Tests:

```text
mail_analyst.py
mail_analyst_gui.py
mailanalyst/
tests/
docs/
    STATUS.md
    01_guides/
    02_reports/
assets/fonts/
build_exe.ps1
requirements.txt
requirements-dev.txt
PROJECT_GOALS.md
AGENTS.md
README.md
.gitignore
.github\copilot-instructions.md
.github\workflows\checks.yml
.agents\skills\mailanalyst-verify\SKILL.md
input_emails\
out\
```

Die beiden Einstiegsskripte delegieren an das Paket `mailanalyst`. Python-Imports erfolgen direkt aus dem Paket, beispielsweise aus `mailanalyst.checks.preflight` und `mailanalyst.checks.system`. Die früheren Kompatibilitätsmodule und Funktions-Reexports aus `mail_analyst.py` wurden entfernt. Fachlogik liegt ausschließlich im Paket. Die Ordner `input_emails` und `out` sind nur Platzhalter. Ihre Inhalte werden nicht ins Repository uebernommen.

## Entwicklung und Tests

Eigene Python-Dateien bleiben bei höchstens 200 physischen Zeilen. Eine Datei hat eine klare Zuständigkeit; GUI-Code und Fachlogik werden getrennt gehalten.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m compileall -q mailanalyst tests
.\.venv\Scripts\python.exe -m pip check
```

Die Tests verwenden ausschließlich synthetische E-Mails. Sie prüfen Parser und Cache, Exporte gegen einen vor der Aufteilung erzeugten Vergleichsbestand, beide CLI-Einstiege, den Tkinter-Workflow, die Dateigröße und die Importstruktur. GitHub Actions führt diese Prüfungen unter Windows aus. Reale MSG-/PST-Archive und große Mailbestände benötigen weiterhin eigene Tests.

Alternativ zum bisherigen CLI-Einstieg funktioniert `python -m mailanalyst` mit denselben Optionen.

Fuer GitHub Copilot liegt eine kurze Projektanweisung unter `.github\copilot-instructions.md`. Sie beschreibt Setup, Run-Kommandos und wichtige Datenregeln fuer dieses Repository.

## Setup

Im Projektordner:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Die `.venv` wird nur lokal erstellt und wird nicht ins Repository uebernommen. Sie ist an Rechner, Pfad und Python-Version gekoppelt und sollte deshalb in jeder Zielumgebung neu erstellt werden.

## Schnellstart nach Git Clone

```powershell
git clone <repo-url>
cd MailAnalyst
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Danach `.eml`-/`.msg`-Dateien oder `.pst`-Archive in den Ordner `input_emails` kopieren und ausfuehren:

```powershell
.\.venv\Scripts\python.exe mail_analyst.py --input input_emails --output out\emails.parquet --list-output out\emails_microsoft_list.csv
```

Dabei wird zusaetzlich eine Logdatei erzeugt:

```text
out\parse_log.txt
```

## Grafische Oberflaeche

```powershell
.\.venv\Scripts\python.exe mail_analyst_gui.py
```

Die Oberflaeche fuehrt durch fuenf Schritte:

1. Automatischen Systemcheck sichten. Er prueft Laufzeit, Kernpakete, Importer, Ausgabeformate, PST-Verarbeitungswege, temporaeren Schreibzugriff und freien Speicherplatz. Optionale fehlende Komponenten erscheinen als Warnung; echte Blocker sperren den weiteren Ablauf.
2. Eingabe, separaten Zielordner, Ausgabeprofil und PST-Backend festlegen.
3. Vorpruefung starten und OK-, Warnungs-, Fehler- sowie ignorierte Quellen sichten. Warnungen koennen ein- oder ausgeschlossen werden; problematische Einzelquellen lassen sich bewusst per Doppelklick einplanen.
4. Ausgewaehlte Quellen mit echter Fortschrittsanzeige verarbeiten.
5. Zusammenfassung und Ergebnistabelle sichten, den vollstaendigen Zielpfad anzeigen oder kopieren sowie Ausgabeordner oder Log oeffnen.

Während eines Systemchecks, einer Vorprüfung oder Verarbeitung ist genau ein Hintergrundauftrag aktiv. Navigation, Eingaben und weitere Starts sind gesperrt. Über **Abbrechen** wird ein Abbruch angefordert; die laufende Parser-/Bibliotheks- oder Schreiboperation darf zunächst sauber zurückkehren. Danach kann der Workflow erneut gestartet werden.

Beim Schließen während eines Auftrags fordert die Anwendung ebenfalls den Abbruch an und wartet sichtbar auf den Worker. Große PST-Parseraufrufe oder blockierende Bibliotheksoperationen können dieses Warten verlängern. Sobald die abschließende Paketveröffentlichung begonnen hat, wird der kurze Abschluss zu Ende geführt; das Fenster schließt danach. Es werden keine Worker gewaltsam beendet.

Die feste Navigation auf der linken Seite zeigt, wo man sich im Ablauf befindet. Ein Schritt wird erst freigeschaltet, wenn er im aktuellen Lauf erreichbar ist. Die Gestaltung basiert ausschliesslich auf dem mit Python gelieferten Tkinter/ttk und benoetigt weder ein Web-Frontend noch ein zusaetzliches UI-Framework.

Die Oberfläche verwendet die lokal gebuendelte Schriftfamilie Mulish sowie die Oberflächenfarben `#414343`, `#D63C24`, `#EF7D00` und `#0090B6`. Die Schrift wird beim Start aus `assets/fonts` nur fuer den laufenden App-Prozess geladen und muss weder in der Entwicklungsumgebung noch auf dem Zielrechner installiert sein. Der Systemcheck bestaetigt, ob Mulish tatsaechlich aktiv ist; nur bei einem Ladefehler verwendet die App Segoe UI als sicheren Fallback. Mulish steht unter der SIL Open Font License; der Lizenztext liegt unter `assets/fonts/OFL.txt` und wird in die portable Anwendung aufgenommen.

Die Vorpruefung kontrolliert Lesbarkeit, Dateigroesse und grundlegende EML-, MSG-/OLE- beziehungsweise PST-Signaturen. Sie schreibt `preflight_report.csv` und `preflight_report.json` in den Zielordner. Parserfehler bleiben davon getrennt und werden weiterhin im Laufprotokoll sowie in den Exportdaten dokumentiert.

Der Systemcheck startet beim Oeffnen der App automatisch. Nach Auswahl eines verwendbaren Zielordners werden seine Ergebnisse als `system_check_report.csv` und `system_check_report.json` gemeinsam mit dem Vorpruefungsbericht dokumentiert.

Fuer Markdown kann vor dem Lauf die Linkdarstellung gewaehlt werden:

- `Vollstaendige URLs`: unveraenderte Darstellung fuer maximale Nachvollziehbarkeit
- `Kompakte URLs`: Bild-URLs entfernen und typische Trackingparameter kuerzen
- `Nur Linktext`: URL-Ziele aus dem Markdown entfernen

Parquet und JSON bleiben davon unberuehrt und enthalten weiterhin die vollstaendigen Masterdaten. Die getroffene Auswahl wird zusammen mit Eingabe, Ausgabeprofil, PST-Backend und Quellenanzahl in `processing_options.json` dokumentiert.

In der Oberflaeche kann eine einzelne `.eml`-, `.msg`- oder `.pst`-Datei oder ein kompletter Ordner ausgewaehlt werden. Fuer PST stehen `Automatisch`, `Ohne Outlook (libpff)` und `Klassisches Outlook` zur Wahl. Nach dem Lauf zeigt eine Tabelle Datum, Absender, Betreff, Quellformat und Parserstatus.

Ueber `Zielordner...` kann die Ausgabe bewusst ausserhalb des Projekt-Repositories abgelegt werden, zum Beispiel auf einem verschluesselten Datentraeger oder in einem separaten Analyse-Workspace. Beim Markdown-Monatsordner liegen die Monatsdateien und Indizes unter `exports/mail_workspace/` des Laufordners; `parse_log.txt` liegt direkt im Laufordner.

Das Ausgabeprofil `Analysepaket` erzeugt gemeinsam Parquet, JSON, Markdown-Monatsdateien, Indizes und Logdatei. Systemcheck und Vorpruefung zeigen vor dem Lauf die verfuegbaren Komponenten und die gefundenen Quellen.

Waehren der Verarbeitung zeigt die Oberflaeche einen Aktivitaetsindikator. Nach einem erfolgreichen Lauf kann der Ausgabeordner direkt geoeffnet werden.

## Windows-EXE bauen

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\build_exe.ps1
```

Die portable Anwendung liegt danach unter `dist\MailAnalyst\MailAnalyst.exe`. Der gesamte Ordner `dist\MailAnalyst` muss zusammen verteilt werden; auf dem Zielrechner ist keine separate Python-Installation erforderlich.

Das Outlook-Backend bindet das Archiv fuer die Dauer des Imports in klassisches Outlook fuer Windows ein und entfernt es danach wieder. Das alternative `libpff`-/`pypff`-Backend liest die PST direkt und benoetigt kein Outlook, muss unter Windows aber separat installiert oder als geprueftes Binary bereitgestellt werden. Bei `Automatisch` wird libpff bevorzugt und andernfalls Outlook verwendet. PST-Dateien werden seriell verarbeitet.

Die Auswahl ist auch auf der Kommandozeile moeglich:

```powershell
python mail_analyst.py --input archiv.pst --output out\emails.parquet --pst-backend outlook
python mail_analyst.py --input archiv.pst --output out\emails.parquet --pst-backend libpff
```

## Input-Pfad

Der Ordner mit den `.eml`-Dateien wird ueber `--input` definiert. Das Skript kann einen Ordner rekursiv durchsuchen oder eine einzelne `.eml`-Datei lesen.

Verwende die vollständige Projektstruktur aus [Dateien im Projekt](README.md#dateien-im-projekt), einschließlich des Pakets `mailanalyst/`. Quelldateien dürfen in Unterordnern von `input_emails/` liegen oder über einen externen Pfad gewählt werden.

Beispiel:

```powershell
.\.venv\Scripts\python.exe mail_analyst.py --input input_emails --output out\emails.parquet --list-output out\emails_microsoft_list.csv
```

Mit absoluten Pfaden:

```powershell
.\.venv\Scripts\python.exe "C:\MailAnalyst\mail_analyst.py" --input "D:\Projektarchiv\E-Mails" --output "C:\MailAnalyst\out\emails.parquet" --list-output "C:\MailAnalyst\out\emails_microsoft_list.csv"
```

## Laufordner und Ergebnisstatus

Jeder GUI-Lauf erzeugt `<Zielordner>/runs/<Zeit>-<UUID>/` mit `manifest.json`, `parse_log.txt`, `processing_options.json` und den geprüften Ausgaben unter `exports/`. Die Ergebnisanzeige öffnet diesen konkreten Laufordner. Für die Weitergabe den vollständigen Laufordner kopieren. Cache und vorläufige System-/Vorprüfungsberichte bleiben im übergeordneten Zielbereich.

Das Manifest kennzeichnet `completed` beziehungsweise `completed_with_errors` als abgeschlossen; bei letzterem die Parserfehler beachten. `running`, `failed` und `cancelled` sind keine vollständigen Ergebnisse. Ein Abbruch vor Veröffentlichung erhält den Status `cancelled`; bereits vorhandene Dateien unter `.pending/` sind unvollständige Zwischenprodukte. Ein zuvor fertig geschriebener Cache kann dabei für den nächsten Lauf erhalten bleiben. Unterbrochene Läufe werden nicht automatisch fortgesetzt. Ein neues Laufpaket vermischt keine früheren Monatsdateien.

Die CLI legt Laufpakete neben dem Masterexport unter `runs/` an. Die bisherigen Pfade für `--output`, `--list-output`, `--markdown-dir` und Log erhalten zusätzliche Kopien. Mehrere explizite Ziele können nicht gemeinsam atomar ersetzt werden; maßgeblich bleibt das Manifest des Laufpakets. Ein vorheriger Markdown-Zielordner bleibt als `.previous-<UUID>` neben dem neuen Ordner erhalten. Quell-, Cache-, Log- und Exportpfade dürfen sich nicht überschneiden.

## Ausgaben

Der Masterexport enthaelt alle extrahierten Daten:

```powershell
python mail_analyst.py --input input_emails --output out\emails.parquet
```

Fuer Kolleginnen und Kollegen bzw. Microsoft Lists kann zusaetzlich eine reduzierte Review-Datei erzeugt werden:

```powershell
python mail_analyst.py --input input_emails --output out\emails.parquet --list-output out\emails_microsoft_list.csv
```

Unterstuetzte Ausgabeformate:

- `.parquet`: empfohlenes Masterformat
- `.csv`: Austauschformat, gut fuer Microsoft Lists
- `.xlsx`: Sichtdatei fuer Excel, lange Zellinhalte werden technisch bedingt gekuerzt
- `.json`: strukturierter Austausch fuer Skripte und Entwicklerwerkzeuge
- `.xml`: strukturierter Austausch mit allen Masterfeldern
- `.md`: gut lesbares Dokument fuer Textsuche und erste Tests mit Coding-Assistenten

CSV und Excel sind geschützte Sichtausgaben: Formelverdächtige CSV-Texte erhalten ein führendes Apostroph, auch im Markdown-CSV-Index und in Prüfberichten. Das betrifft unter anderem Texte mit `=`, `+`, `-` oder `@` am Anfang, einschließlich führender Leer-/Steuerzeichen. Echte numerische Werte bleiben Zahlen. Excel speichert Zeichenfolgen ausdrücklich als Textzellen. JSON, Parquet, JSONL-Indizes und der interne Masterbestand behalten die ursprünglichen Texte. Für eine unveränderte maschinelle Weiterverarbeitung diese strukturierten Formate verwenden.

Markdown kann auch direkt ueber die Kommandozeile erzeugt werden:

```powershell
python mail_analyst.py --input input_emails --output out\emails.md
```

Fuer grosse Datenmengen kann ein durchsuchbarer Markdown-Datensatz nach Monaten erzeugt werden:

```powershell
python mail_analyst.py --input input_emails --output out\emails.parquet --markdown-dir out\mail_workspace
```

Dabei entstehen Jahresordner mit einer Markdown-Datei pro Monat sowie `index.csv` und `index.jsonl`. Der Index enthaelt unter anderem Zeitraum, Absender, Empfaenger, CC, Betreff, Message-ID, Anlagen und den Verweis auf die zugehoerige Markdown-Stelle.

## Logdatei

Standardmaessig schreibt das Skript eine Logdatei neben den Masterexport:

```text
out\parse_log.txt
```

Im CLI-Workflow enthaelt die Logdatei Startzeit, Input-/Output-Pfade, Cache-Pfad, Optionen, verarbeitete Dateien, Erfolgs-/Fehleranzahl und bei Fehlern die betroffene Datei mit Fehlermeldung.

Jeder Lauf schreibt sein eigenes `parse_log.txt` mit Start, Optionen, Quellenfortschritt und Abschlusszahlen in den Laufordner. Auch reine Cacheläufe erhalten eine Zusammenfassung. `manifest.json` dokumentiert Quellenprüfungen, Exportdateien und Status; die GUI speichert daneben `processing_options.json`.

Ein anderer Logpfad kann explizit angegeben werden:

```powershell
python mail_analyst.py --input input_emails --output out\emails.parquet --list-output out\emails_microsoft_list.csv --log-output out\mein_parse_log.txt
```

## Cache

Die GUI legt den Cache unter `<Zielordner>/.mailanalyst_cache/mail_metadata.sqlite3` ab. Die CLI verwendet denselben relativen Standardpfad im Arbeitsordner oder einen expliziten Pfad über `--cache`. SQLite enthält versionierte JSON-Daten; alte Pickle-Caches werden nicht geladen. Ein bisheriger `.pkl`-/`.pickle`-Pfad wird auf `.sqlite3` umgestellt, das Original bleibt erhalten. Beschädigte oder inkompatible Caches werden mit Warnung neu aufgebaut.

Geänderte Zeitzonen, Schema-/Parserrevisionen und das tatsächlich gewählte PST-Backend machen Cachetreffer ungültig. Frisch geparste Quellen werden vor und nach dem Lesen gehasht. Ohne `--hash-check` bleiben schnelle Cachetreffer ausdrücklich ungeprüft; der frühere Hash wird im Manifest als `reused_unverified` gekennzeichnet.

Cache komplett neu aufbauen:

```powershell
python mail_analyst.py --input input_emails --output out\emails.parquet --refresh
```

Strengere Cache-Pruefung mit SHA-256:

```powershell
python mail_analyst.py --input input_emails --output out\emails.parquet --hash-check
```

## Deutsche Datumsfelder

Die Review-/Listenansicht enthaelt u. a.:

- `Gesendet am`
- `Datum`
- `Uhrzeit`
- `Jahr`
- `Monat`
- `Monatsname`
- `Jahr-Monat`
- `Quartal`
- `Kalenderwoche`
- `ISO-Jahr`
- `Wochentag`

Die Berechnung erfolgt standardmaessig in `Europe/Berlin`:

```powershell
python mail_analyst.py --input input_emails --output out\emails.parquet --timezone Europe/Berlin
```

## Body-Text

Der Masterexport enthaelt mehrere Body-Felder:

- `body_text_raw`: extrahierter Plaintext, moeglichst nah am E-Mail-Inhalt
- `body_text_clean`: bereinigte Fassung fuer Suche und Review
- `body_text`: Alias auf `body_text_clean`
- `body_html`: HTML-Body, falls vorhanden

Wenn keine Plaintext-Version vorhanden ist, wird HTML in lesbaren Plaintext umgewandelt.
