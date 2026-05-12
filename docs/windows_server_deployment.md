# Guía de Despliegue en Windows Server

## Requisitos

- Windows Server 2019 / 2022
- Python 3.12+
- NSSM 2.24+ (para servicio Windows)
- IIS (opcional, para reverse proxy)

---

## 1. Instalación de Python

1. Descargar Python 3.12+ desde https://www.python.org/downloads/
2. Ejecutar instalador con opción **"Add Python to PATH"** marcada
3. Verificar instalación:
```powershell
python --version
# Python 3.12.x
```

---

## 2. Clonar / Copiar el Proyecto

```powershell
# Copiar proyecto al servidor
xcopy /E /I sql-risk-engine C:\Apps\sql-risk-engine
cd C:\Apps\sql-risk-engine
```

---

## 3. Crear Entorno Virtual e Instalar Dependencias

```powershell
cd C:\Apps\sql-risk-engine

# Crear virtualenv
python -m venv .venv

# Activar
.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Configurar Variables de Entorno

```powershell
# Copiar plantilla
Copy-Item .env.example .env

# Editar .env con Notepad
notepad .env
```

Valores recomendados para producción:
```env
APP_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
LOG_FILE=C:\Apps\sql-risk-engine\logs\sql-risk-engine.log
APPROVAL_THRESHOLD=60
```

---

## 5. Ejecutar Manualmente (Prueba)

```powershell
cd C:\Apps\sql-risk-engine
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Verificar en navegador: `http://localhost:8000/docs`

---

## 6. Instalar como Servicio Windows con NSSM

### 6.1 Descargar NSSM

Descargar desde https://nssm.cc/download y colocar `nssm.exe` en `C:\Tools\nssm\`

### 6.2 Crear el Servicio

```powershell
# Ejecutar como Administrador
C:\Tools\nssm\nssm.exe install SqlRiskEngine

# En la UI de NSSM configurar:
# Application Path: C:\Apps\sql-risk-engine\.venv\Scripts\python.exe
# Startup directory: C:\Apps\sql-risk-engine
# Arguments: -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

# O via línea de comandos:
C:\Tools\nssm\nssm.exe install SqlRiskEngine `
    "C:\Apps\sql-risk-engine\.venv\Scripts\python.exe" `
    "-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"

C:\Tools\nssm\nssm.exe set SqlRiskEngine AppDirectory "C:\Apps\sql-risk-engine"
C:\Tools\nssm\nssm.exe set SqlRiskEngine DisplayName "SQL Risk Engine"
C:\Tools\nssm\nssm.exe set SqlRiskEngine Description "Microservicio de análisis de riesgo SQL"
C:\Tools\nssm\nssm.exe set SqlRiskEngine Start SERVICE_AUTO_START
C:\Tools\nssm\nssm.exe set SqlRiskEngine AppStdout "C:\Apps\sql-risk-engine\logs\stdout.log"
C:\Tools\nssm\nssm.exe set SqlRiskEngine AppStderr "C:\Apps\sql-risk-engine\logs\stderr.log"
```

### 6.3 Iniciar / Detener el Servicio

```powershell
# Iniciar
Start-Service SqlRiskEngine
# o
C:\Tools\nssm\nssm.exe start SqlRiskEngine

# Detener
Stop-Service SqlRiskEngine

# Reiniciar
Restart-Service SqlRiskEngine

# Ver estado
Get-Service SqlRiskEngine
```

---

## 7. Configurar Firewall de Windows

```powershell
# Abrir puerto 8000 (ejecutar como Administrador)
New-NetFirewallRule `
    -DisplayName "SQL Risk Engine API" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 8000 `
    -Action Allow

# Verificar regla
Get-NetFirewallRule -DisplayName "SQL Risk Engine API"
```

---

## 8. Configurar IIS como Reverse Proxy (Opcional)

### 8.1 Instalar módulos necesarios

```powershell
# Instalar URL Rewrite y ARR desde Web Platform Installer
# O descargar manualmente:
# - URL Rewrite: https://www.iis.net/downloads/microsoft/url-rewrite
# - Application Request Routing (ARR): https://www.iis.net/downloads/microsoft/application-request-routing
```

### 8.2 Configurar web.config en IIS

Crear `C:\inetpub\wwwroot\sqlriskengine\web.config`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="ReverseProxy_SqlRiskEngine" stopProcessing="true">
                    <match url="(.*)" />
                    <action type="Rewrite" url="http://localhost:8000/{R:1}" />
                    <serverVariables>
                        <set name="HTTP_X_FORWARDED_HOST" value="{HTTP_HOST}" />
                    </serverVariables>
                </rule>
            </rules>
        </rewrite>
    </system.webServer>
</configuration>
```

---

## 9. Monitorear Logs

```powershell
# Ver logs en tiempo real
Get-Content "C:\Apps\sql-risk-engine\logs\sql-risk-engine.log" -Wait -Tail 50

# Ver últimas 100 líneas
Get-Content "C:\Apps\sql-risk-engine\logs\sql-risk-engine.log" -Tail 100

# Buscar errores
Select-String -Path "C:\Apps\sql-risk-engine\logs\*.log" -Pattern '"level":"ERROR"'

# Ver logs del servicio NSSM
Get-Content "C:\Apps\sql-risk-engine\logs\stderr.log" -Tail 50
```

---

## 10. Actualizar Versión

```powershell
# 1. Detener servicio
Stop-Service SqlRiskEngine

# 2. Hacer backup
Copy-Item -Recurse C:\Apps\sql-risk-engine C:\Backup\sql-risk-engine-$(Get-Date -Format 'yyyyMMdd')

# 3. Copiar nuevos archivos (mantener .env y logs)
xcopy /E /I /Y nueva-version\* C:\Apps\sql-risk-engine\ /EXCLUDE:exclude.txt

# 4. Actualizar dependencias
cd C:\Apps\sql-risk-engine
.venv\Scripts\pip.exe install -r requirements.txt --upgrade

# 5. Reiniciar servicio
Start-Service SqlRiskEngine

# 6. Verificar health
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/health"
```

---

## 11. Variables de Entorno del Sistema (Alternativa a .env)

```powershell
# Configurar como variables de sistema (persistentes)
[System.Environment]::SetEnvironmentVariable("APP_ENV", "production", "Machine")
[System.Environment]::SetEnvironmentVariable("PORT", "8000", "Machine")
[System.Environment]::SetEnvironmentVariable("LOG_LEVEL", "INFO", "Machine")
[System.Environment]::SetEnvironmentVariable("APPROVAL_THRESHOLD", "60", "Machine")
```

---

## 12. Checklist de Producción

- [ ] Python 3.12+ instalado
- [ ] Entorno virtual creado en `.venv`
- [ ] Dependencias instaladas con `pip install -r requirements.txt`
- [ ] Archivo `.env` configurado con valores de producción
- [ ] Directorio `logs/` con permisos de escritura
- [ ] Puerto 8000 abierto en firewall
- [ ] Servicio NSSM `SqlRiskEngine` creado y en AUTO_START
- [ ] Servicio iniciado y verificado con `Get-Service SqlRiskEngine`
- [ ] Health check exitoso: `Invoke-RestMethod -Method POST http://localhost:8000/health`
- [ ] Swagger accesible: http://servidor:8000/docs
