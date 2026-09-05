# MailAnalyst

Ein lokales Python-Werkzeug, um Outlook-E-Mails aus `.eml`, `.msg` und `.pst` auszulesen und strukturiert bereitzustellen. Neben der Kommandozeile gibt es eine minimalistische Desktop-Oberflaeche.

Die [Projektziele](PROJECT_GOALS.md) beschreiben den fachlichen Nutzen, den vorgesehenen Umfang und offene Festlegungen. Der [Reviewbericht](REVIEW_REPORT.md) dokumentiert den technischen Stand und die empfohlenen nächsten Schritte.

## Dateien im Projekt

Das Projekt besteht bewusst nur aus:

```text
mail_analyst.py
mail_analyst_gui.py
requirements.txt
README.md
.gitignore
.github\copilot-instructions.md
input_emails\
out\
```

Die Ordner `input_emails` und `out` sind nur Platzhalter. Ihre Inhalte werden nicht ins Repository uebernommen.

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

Die feste Navigation auf der linken Seite zeigt, wo man sich im Ablauf befindet. Ein Schritt wird erst freigeschaltet, wenn er im aktuellen Lauf erreichbar ist. Die Gestaltung basiert ausschliesslich auf dem mit Python gelieferten Tkinter/ttk und benoetigt weder ein Web-Frontend noch ein zusaetzliches UI-Framework.

Die Oberfläche verwendet die lokal gebuendelte Schriftfamilie Mulish sowie die Oberflächenfarben `#414343`, `#D63C24`, `#EF7D00` und `#0090B6`. Die Schrift wird beim Start aus `assets/fonts` nur fuer den laufenden App-Prozess geladen und muss weder in der Entwicklungsumgebung noch auf dem Zielrechner installiert sein. Der Systemcheck bestaetigt, ob Mulish tatsaechlich aktiv ist; nur bei einem Ladefehler verwendet die App Segoe UI als sicheren Fallback. Mulish steht unter der SIL Open Font License; der Lizenztext liegt unter `assets/fonts/OFL.txt` und wird in die portable Anwendung aufgenommen.

Die Vorpruefung kontrolliert Lesbarkeit, Dateigroesse und grundlegende EML-, MSG-/OLE- beziehungsweise PST-Signaturen. Sie schreibt `preflight_report.csv` und `preflight_report.json` in den Zielordner. Parserfehler bleiben davon getrennt und werden weiterhin im Laufprotokoll sowie in den Exportdaten dokumentiert.

Der Systemcheck startet beim Oeffnen der App automatisch. Nach Auswahl eines verwendbaren Zielordners werden seine Ergebnisse als `system_check_report.csv` und `system_check_report.json` gemeinsam mit dem Vorpruefungsbericht dokumentiert.

Fuer Markdown kann vor dem Lauf die Linkdarstellung gewaehlt werden:

- `Vollstaendige URLs`: unveraenderte Darstellung fuer maximale Nachvollziehbarkeit
- `Kompakte URLs`: Bild-URLs entfernen und typische Trackingparameter kuerzen
- `Nur Linktext`: URL-Ziele aus dem Markdown entfernen

Parquet und JSON bleiben davon unberuehrt und enthalten weiterhin die vollstaendigen Masterdaten. Die getroffene Auswahl wird zusammen mit Eingabe, Ausgabeprofil, PST-Backend und Quellenanzahl in `processing_options.json` dokumentiert.

In der Oberflaeche kann eine einzelne `.eml`-, `.msg`- oder `.pst`-Datei oder ein kompletter Ordner ausgewaehlt werden. Fuer PST stehen `Automatisch`, `Ohne Outlook (libpff)` und `Klassisches Outlook` zur Wahl. Nach dem Lauf zeigt eine Tabelle Datum, Absender, Betreff, Anlagen, Quellformat und Parserstatus.

Ueber `Zielordner...` kann die Ausgabe bewusst ausserhalb des Projekt-Repositories abgelegt werden, zum Beispiel auf einem verschluesselten Datentraeger oder in einem separaten Analyse-Workspace. Beim Markdown-Monatsordner liegen Monatsdateien, Indizes und `parse_log.txt` gemeinsam im uebertragbaren Zielordner.

Das Ausgabeprofil `Analysepaket` erzeugt gemeinsam Parquet, JSON, Markdown-Monatsdateien, Indizes und Logdatei. `Pruefen` zeigt vor dem Lauf Anzahl, Formate und Gesamtgroesse der gefundenen Quellen. Die Statuszeile zeigt ausserdem die lokal verfuegbaren Import-Backends.

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

Empfohlene Arbeitsstruktur:

```text
C:\MailAnalyst\
|-- mail_analyst.py
|-- requirements.txt
|-- README.md
|-- input_emails\
|   |-- mail_001.eml
|   |-- mail_002.eml
|   `-- unterordner\
|       `-- mail_003.eml
`-- out\
```

Beispiel:

```powershell
.\.venv\Scripts\python.exe mail_analyst.py --input input_emails --output out\emails.parquet --list-output out\emails_microsoft_list.csv
```

Mit absoluten Pfaden:

```powershell
.\.venv\Scripts\python.exe "C:\MailAnalyst\mail_analyst.py" --input "D:\Projektarchiv\E-Mails" --output "C:\MailAnalyst\out\emails.parquet" --list-output "C:\MailAnalyst\out\emails_microsoft_list.csv"
```

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

Die Logdatei enthaelt Startzeit, Input-/Output-Pfade, Cache-Pfad, Optionen, verarbeitete Dateien, Erfolgs-/Fehleranzahl und bei Fehlern die betroffene Datei mit Fehlermeldung.

Ein anderer Logpfad kann explizit angegeben werden:

```powershell
python mail_analyst.py --input input_emails --output out\emails.parquet --list-output out\emails_microsoft_list.csv --log-output out\mein_parse_log.txt
```

## Cache

Standardmaessig wird beim Lauf ein Cache unter `.mailanalyst_cache\mail_metadata.pkl` erstellt. Dadurch werden unveraenderte E-Mails beim naechsten Lauf nicht erneut geparst.

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
