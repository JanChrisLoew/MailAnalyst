# MailAnalyst Copilot Instructions

## Project Context

This repository contains a small Python CLI for parsing exported Outlook/MailStore `.eml` files into structured tabular data.

The project is intentionally lightweight:

- Main script: `mail_analyst.py`
- Dependencies: `requirements.txt`
- User documentation: `README.md`
- Input placeholder: `input_emails/`
- Output placeholder: `out/`

Do not add a web app, database, package framework, or complex project structure unless explicitly requested.

## Main Workflow

Use this setup after cloning:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the parser with:

```powershell
.\.venv\Scripts\python.exe mail_analyst.py --input input_emails --output out\emails.parquet --list-output out\emails_microsoft_list.csv
```

Run a full rebuild with:

```powershell
.\.venv\Scripts\python.exe mail_analyst.py --input input_emails --output out\emails.parquet --list-output out\emails_microsoft_list.csv --refresh
```

Validate syntax with:

```powershell
.\.venv\Scripts\python.exe -m py_compile mail_analyst.py
```

## Data Handling Rules

- Only `.eml` files are supported by design.
- Do not commit real email files, generated exports, caches, or `.venv`.
- `input_emails/` and `out/` are placeholder folders; keep their `.gitkeep` files.
- Keep full data in Parquet as the master output.
- Use the CSV list export for Microsoft Lists or human review.

## Domain Requirements

The tool is used for project claim/evidence work. Preserve traceability:

- Keep `source_path`, `file_sha256`, `message_id`, `sent_at_utc`, and parser status fields.
- Do not silently drop parse errors; record them in `parse_status` and `parse_error`.
- Preserve original body variants where possible: `body_text_raw`, `body_text_clean`, `body_html`.
- German review fields are important: `Datum`, `Jahr`, `Monat`, `Kalenderwoche`, `Wochentag`.
- Date derivations should use `Europe/Berlin` unless the user explicitly changes `--timezone`.

## Coding Style

- Keep changes in `mail_analyst.py` unless there is a clear reason to add another file.
- Prefer simple, explicit functions over abstractions.
- Keep comments short and practical.
- Use ASCII in files where possible.
- Do not introduce destructive file operations.
- If changing output columns, update `README.md` and keep the Microsoft Lists export stable where possible.
