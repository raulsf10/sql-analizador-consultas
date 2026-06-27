import psycopg2
import psycopg2.extras
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.config.settings import settings
from app.db import catalog_repository
from app.db.database import connect
from app.models.catalog_models import (
    CatalogoItemResponse,
    CatalogoCreateRequest,
    CatalogoUpdateRequest,
    CatalogoListResponse,
)

router = APIRouter(tags=["Catálogo"])

_tablas_router = APIRouter(prefix="/catalogo/tablas")
_rutas_router = APIRouter(prefix="/catalogo/rutas")


def _get_conn():
    return connect(settings.database_url, cursor_factory=psycopg2.extras.RealDictCursor)


def _row_to_response(row: dict) -> CatalogoItemResponse:
    return CatalogoItemResponse(
        id=row["id"],
        tipo=row["tipo"],
        nombre=row["nombre"],
        descripcion=row["descripcion"],
        activo=row["activo"],
        creado_en=str(row["creado_en"]),
    )


def _list(tipo: str, activo: Optional[bool]) -> CatalogoListResponse:
    query = "SELECT * FROM catalogo_criticos WHERE tipo = %s"
    params: list = [tipo]
    if activo is not None:
        query += " AND activo = %s"
        params.append(activo)
    query += " ORDER BY nombre"

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
    finally:
        conn.close()

    items = [_row_to_response(r) for r in rows]
    return CatalogoListResponse(total=len(items), items=items)


def _get_one(item_id: int, tipo: str) -> CatalogoItemResponse:
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM catalogo_criticos WHERE id = %s AND tipo = %s",
                (item_id, tipo),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail=f"No se encontró el elemento con id={item_id}")
    return _row_to_response(row)


def _create(tipo: str, body: CatalogoCreateRequest) -> CatalogoItemResponse:
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO catalogo_criticos (tipo, nombre, descripcion) VALUES (%s, %s, %s) RETURNING *",
                    (tipo, body.nombre.upper(), body.descripcion),
                )
                row = cur.fetchone()
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                raise HTTPException(
                    status_code=409,
                    detail=f"Ya existe un elemento con nombre='{body.nombre}' en el catálogo de {tipo}",
                )
        conn.commit()
    finally:
        conn.close()

    catalog_repository.load_catalog(settings.database_url)
    return _row_to_response(row)


def _update(item_id: int, tipo: str, body: CatalogoUpdateRequest) -> CatalogoItemResponse:
    if body.nombre is None and body.descripcion is None and body.activo is None:
        raise HTTPException(status_code=422, detail="Debe enviar al menos un campo para actualizar")

    fields: list[str] = []
    params: list = []

    if body.nombre is not None:
        fields.append("nombre = %s")
        params.append(body.nombre.upper())
    if body.descripcion is not None:
        fields.append("descripcion = %s")
        params.append(body.descripcion)
    if body.activo is not None:
        fields.append("activo = %s")
        params.append(body.activo)

    params.extend([item_id, tipo])

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE catalogo_criticos SET {', '.join(fields)} WHERE id = %s AND tipo = %s RETURNING *",
                params,
            )
            row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail=f"No se encontró el elemento con id={item_id}")

    catalog_repository.load_catalog(settings.database_url)
    return _row_to_response(row)


def _delete(item_id: int, tipo: str) -> None:
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM catalogo_criticos WHERE id = %s AND tipo = %s RETURNING id",
                (item_id, tipo),
            )
            deleted = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    if deleted is None:
        raise HTTPException(status_code=404, detail=f"No se encontró el elemento con id={item_id}")

    catalog_repository.load_catalog(settings.database_url)


# ── /catalogo/tablas ──────────────────────────────────────────────────────────

@_tablas_router.get("", response_model=CatalogoListResponse, summary=" ")
def list_tablas(activo: Optional[bool] = Query(default=None, description="Filtrar por estado activo")):
    return _list("TABLA", activo)


@_tablas_router.get("/{item_id}", response_model=CatalogoItemResponse, summary=" ")
def get_tabla(item_id: int):
    return _get_one(item_id, "TABLA")


@_tablas_router.post("", response_model=CatalogoItemResponse, status_code=201, summary=" ")
def create_tabla(body: CatalogoCreateRequest):
    return _create("TABLA", body)


@_tablas_router.put("/{item_id}", response_model=CatalogoItemResponse, summary=" ")
def update_tabla(item_id: int, body: CatalogoUpdateRequest):
    return _update(item_id, "TABLA", body)


@_tablas_router.delete("/{item_id}", status_code=204, summary=" ")
def delete_tabla(item_id: int):
    _delete(item_id, "TABLA")


# ── /catalogo/rutas ───────────────────────────────────────────────────────────

@_rutas_router.get("", response_model=CatalogoListResponse, summary=" ")
def list_rutas(activo: Optional[bool] = Query(default=None, description="Filtrar por estado activo")):
    return _list("WF", activo)


@_rutas_router.get("/{item_id}", response_model=CatalogoItemResponse, summary=" ")
def get_ruta(item_id: int):
    return _get_one(item_id, "WF")


@_rutas_router.post("", response_model=CatalogoItemResponse, status_code=201, summary=" ")
def create_ruta(body: CatalogoCreateRequest):
    return _create("WF", body)


@_rutas_router.put("/{item_id}", response_model=CatalogoItemResponse, summary=" ")
def update_ruta(item_id: int, body: CatalogoUpdateRequest):
    return _update(item_id, "WF", body)


@_rutas_router.delete("/{item_id}", status_code=204, summary=" ")
def delete_ruta(item_id: int):
    _delete(item_id, "WF")


router.include_router(_tablas_router)
router.include_router(_rutas_router)
