param([string]$PythonPath = "")
$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if ($PythonPath) { $Python = (Resolve-Path -LiteralPath $PythonPath).Path }

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Virtuelle Umgebung fehlt. Bitte zuerst python -m venv .venv ausfuehren."
}

$BuildInfo = Join-Path $ProjectDir "out\build-metadata\build_info.json"
Push-Location $ProjectDir
try {
& $Python -m scripts.write_build_info --output $BuildInfo
if ($LASTEXITCODE -ne 0) { throw "Buildmetadaten fehlgeschlagen" }
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --name MailAnalyst `
    --paths $ProjectDir `
    --collect-all extract_msg `
    --collect-all pyarrow `
    --hidden-import pypff `
    --hidden-import win32timezone `
    --add-data "$ProjectDir\assets\fonts;assets\fonts" `
    --add-data "$ProjectDir\.venv\Lib\site-packages\libpff_python_windows-20231205.dist-info\licenses;licenses\libpff" `
    --add-data "$BuildInfo;." `
    (Join-Path $ProjectDir "mail_analyst_gui.py")

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller-Build fehlgeschlagen (Exitcode $LASTEXITCODE). Ist MailAnalyst.exe noch geoeffnet?"
}
Copy-Item -LiteralPath $BuildInfo -Destination (Join-Path $ProjectDir "dist\MailAnalyst\build_info.json")
Copy-Item -LiteralPath (Join-Path $ProjectDir "RELEASE_NOTES.md") -Destination (Join-Path $ProjectDir "dist\MailAnalyst\RELEASE_NOTES.md")
& $Python -m scripts.package_manifest (Join-Path $ProjectDir "dist\MailAnalyst")
if ($LASTEXITCODE -ne 0) { throw "Paketpruefsummen fehlgeschlagen" }
} finally { Pop-Location }

Write-Host "Fertig: $ProjectDir\dist\MailAnalyst\MailAnalyst.exe"
