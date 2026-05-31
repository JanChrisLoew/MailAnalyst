# MailAnalyst

Ein einzelnes Python-Skript, um exportierte Outlook-/Mailstore-E-Mails im `.eml`-Format auszulesen und als strukturierte Tabelle bereitzustellen.

## Dateien im Projekt

Das Projekt besteht bewusst nur aus:

```text
mail_analyst.py
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

Danach die `.eml`-Dateien in den Ordner `input_emails` kopieren und ausfuehren:

```powershell
.\.venv\Scripts\python.exe mail_analyst.py --input input_emails --output out\emails.parquet --list-output out\emails_microsoft_list.csv
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
