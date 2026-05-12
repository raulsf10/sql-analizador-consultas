# start.ps1 - Iniciar el servicio SQL Risk Engine
param(
    [string]$BindHost = "0.0.0.0",
    [int]$Port = 8000,
    [int]$Workers = 1,
    [switch]$Reload
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path ".venv")) {
    Write-Error "Entorno virtual no encontrado. Ejecuta scripts\install.ps1 primero."
    exit 1
}

$UvicornArgs = @(
    "-m", "uvicorn",
    "app.main:app",
    "--host", $BindHost,
    "--port", $Port.ToString(),
    "--workers", $Workers.ToString(),
    "--log-level", "info"
)

if ($Reload) {
    $UvicornArgs += "--reload"
    Write-Host "Modo desarrollo (--reload) activado" -ForegroundColor Yellow
}

Write-Host "=== Iniciando SQL Risk Engine ===" -ForegroundColor Cyan
Write-Host "URL: http://${BindHost}:${Port}"
Write-Host "Swagger: http://${BindHost}:${Port}/docs"

& ".venv\Scripts\python.exe" @UvicornArgs
