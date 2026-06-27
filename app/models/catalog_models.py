from pydantic import BaseModel, Field
from typing import Optional


class CatalogoItemResponse(BaseModel):
    id: int
    tipo: str
    nombre: str
    descripcion: Optional[str]
    activo: bool
    creado_en: str


class CatalogoCreateRequest(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre exacto de la tabla o workflow")
    descripcion: Optional[str] = Field(default=None, description="Descripción opcional")


class CatalogoUpdateRequest(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1)
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class CatalogoListResponse(BaseModel):
    total: int
    items: list[CatalogoItemResponse]
