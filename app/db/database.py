import psycopg2
from urllib.parse import urlparse, unquote

_SCHEMA = """
CREATE TABLE IF NOT EXISTS catalogo_criticos (
    id          SERIAL PRIMARY KEY,
    tipo        VARCHAR(10)  NOT NULL CHECK (tipo IN ('TABLA', 'WF')),
    nombre      TEXT         NOT NULL,
    descripcion TEXT,
    activo      BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en   TIMESTAMP    NOT NULL DEFAULT NOW(),
    UNIQUE (tipo, nombre)
);
"""


def connect(database_url: str, cursor_factory=None):
    r = urlparse(database_url)
    kwargs = dict(
        host=r.hostname,
        port=r.port or 5432,
        dbname=r.path.lstrip("/"),
        user=unquote(r.username or ""),
        password=unquote(r.password or ""),
    )
    if cursor_factory is not None:
        kwargs["cursor_factory"] = cursor_factory
    return psycopg2.connect(**kwargs)


def init_db(database_url: str) -> None:
    """Create schema if it doesn't exist."""
    conn = connect(database_url)
    try:
        with conn.cursor() as cur:
            cur.execute(_SCHEMA)
        conn.commit()
    finally:
        conn.close()
