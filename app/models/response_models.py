from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Severity(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class Criticality(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class Issue(BaseModel):
    codigo: str = Field(..., description="Identificador único de la regla")
    severidad: Severity = Field(..., description="Nivel de severidad del problema")
    mensaje: str = Field(..., description="Descripción del problema encontrado")
    linea: Optional[int] = Field(None, description="Línea donde se encontró el problema")
    recomendacion: str = Field(..., description="Corrección sugerida")
    puntuacion: int = Field(..., description="Puntos de riesgo aportados por esta regla")


class Statistics(BaseModel):
    tablasAfectadas: int = Field(default=0)
    sentenciasDelete: int = Field(default=0)
    sentenciasUpdate: int = Field(default=0)
    sentenciasSelect: int = Field(default=0)
    sentenciasInsert: int = Field(default=0)
    sentenciasDrop: int = Field(default=0)
    sentenciasTruncate: int = Field(default=0)
    totalSentencias: int = Field(default=0)


class AnalyzeResponse(BaseModel):
    exitoso: bool = Field(default=True)
    criticidad: Criticality
    puntuacion: int = Field(..., ge=0, le=100)
    requiereAprobacion: bool
    problemas: List[Issue]
    estadisticas: Statistics
    dialecto: str
    tiempoEjecucionMs: float


class ConsultaXmlResult(BaseModel):
    nombre: str = Field(..., description="Nombre de la transformación en el XML")
    dialecto: str
    puntuacion: int = Field(..., ge=0, le=100)
    criticidad: Criticality
    requiereAprobacion: bool
    problemas: List[Issue]
    estadisticas: Statistics
    tiempoEjecucionMs: float


class XmlAnalyzeResponse(BaseModel):
    exitoso: bool = Field(default=True)
    totalConsultas: int
    criticidadGeneral: Criticality = Field(..., description="Criticidad más alta entre todas las consultas")
    puntuacionMaxima: int = Field(..., ge=0, le=100, description="Puntuación más alta entre todas las consultas")
    consultasCriticas: int = Field(..., description="Número de consultas que requieren aprobación")
    requiereAprobacion: bool = Field(..., description="True si al menos una consulta requiere aprobación")
    consultas: List[ConsultaXmlResult]
    tiempoTotalMs: float
