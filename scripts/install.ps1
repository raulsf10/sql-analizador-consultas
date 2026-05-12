# install.ps1 - Setup del entorno virtual e instalacion de dependencias
param(
    [string]$PythonPath = "python"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=== SQL Risk Engine - Instalacion ===" -ForegroundColor Cyan
Write-Host "Directorio del proyecto: $ProjectRoot"

Set-Location $ProjectRoot

Write-Host "`n[1/4] Verificando Python..." -ForegroundColor Yellow
& $PythonPath --version
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python no encontrado. Instala Python 3.12+ y agrega al PATH."
    exit 1
}

Write-Host "`n[2/4] Creando entorno virtual (.venv)..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "Entorno virtual ya existe, omitiendo creacion."
} else {
    & $PythonPath -m venv .venv
}

Write-Host "`n[3/4] Instalando dependencias..." -ForegroundColor Yellow
& ".venv\Scripts\python.exe" -m pip install --upgrade pip
& ".venv\Scripts\pip.exe" install -r requirements.txt

Write-Host "`n[4/4] Configurando .env..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ".env creado desde .env.example"
} else {
    Write-Host ".env ya existe, omitiendo."
}

Write-Host "`n=== Instalacion completada ===" -ForegroundColor Green
Write-Host "Para ejecutar: .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
