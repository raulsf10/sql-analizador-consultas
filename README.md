# SQL Analizador de Consultas

API para análisis de riesgo de scripts SQL. Recibe un script y retorna un score de criticidad con los hallazgos detectados.

---

## Requisitos

- Python 3.12
- pip

---

## Instalación

```powershell
py -3.12 -m venv .venv

.venv\Scripts\python.exe -m pip install --upgrade pip

.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copia el archivo de configuración:

```powershell
Copy-Item .env.example .env
```

---

## Ejecución

```powershell
.\scripts\start.ps1 -Reload
```

O manualmente:

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger disponible en: `http://localhost:8000/docs`

---

## Endpoint

```
POST /analyze
Content-Type: application/json

{
  "dialect": "oracle",
  "script": "DELETE FROM tabla"
}
```

Dialectos soportados: `oracle`, `tsql`, `postgres`, `mysql`

---

## Variables de entorno (.env)

| Variable           | Default                  |
|--------------------|--------------------------|
| APP_ENV            | production               |
| PORT               | 8000                     |
| LOG_LEVEL          | INFO                     |
| LOG_FILE           | logs/sql-analizador-consultas.log |
| APPROVAL_THRESHOLD | 60                       |
