$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Virtuelle Umgebung fehlt. Bitte zuerst python -m venv .venv ausfuehren."
}

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --name MailAnalyst `
    --collect-all extract_msg `
    --collect-all pyarrow `
    --hidden-import win32timezone `
    --add-data "$ProjectDir\assets\fonts;assets\fonts" `
    (Join-Path $ProjectDir "mail_analyst_gui.py")

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller-Build fehlgeschlagen (Exitcode $LASTEXITCODE). Ist MailAnalyst.exe noch geoeffnet?"
}

Write-Host "Fertig: $ProjectDir\dist\MailAnalyst\MailAnalyst.exe"
