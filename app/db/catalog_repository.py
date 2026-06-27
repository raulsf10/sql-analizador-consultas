from typing import Optional

from app.db.database import connect

_critical_tables: set[str] = set()
_critical_wfs: set[str] = set()


def load_catalog(database_url: str) -> None:
    """Load all active catalog entries into memory. Must be called once at startup."""
    conn = connect(database_url)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT tipo, nombre FROM catalogo_criticos WHERE activo = TRUE")
            rows = cur.fetchall()
    finally:
        conn.close()

    global _critical_tables, _critical_wfs
    _critical_tables = {r[1].upper() for r in rows if r[0] == "TABLA"}
    _critical_wfs = {r[1].upper() for r in rows if r[0] == "WF"}


def get_critical_tables() -> set[str]:
    return _critical_tables


def get_critical_wfs() -> set[str]:
    return _critical_wfs


def find_critical_wf(ruta: str) -> Optional[str]:
    """Return the first critical WF name found inside ruta (case-insensitive), or None."""
    ruta_upper = ruta.upper()
    for wf in _critical_wfs:
        if wf in ruta_upper:
            return wf
    return None
