import time
import xml.etree.ElementTree as ET
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from app.models.request_models import AnalyzeRequest, _DIALECT_MAP
from app.models.response_models import (
    ConsultaXmlResult,
    XmlAnalyzeResponse,
    Criticality,
)
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

_CRITICALITY_ORDER = [
    Criticality.BAJA,
    Criticality.MEDIA,
    Criticality.ALTA,
    Criticality.CRITICA,
]


def _max_criticality(levels: list[Criticality]) -> Criticality:
    if not levels:
        return Criticality.BAJA
    return max(levels, key=lambda c: _CRITICALITY_ORDER.index(c))


def _extract_queries(xml_bytes: bytes) -> list[tuple[str, str]]:
    """Return list of (transformation_name, sql_query) from PowerMart XML."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise HTTPException(status_code=422, detail=f"XML inválido: {exc}")

    results: list[tuple[str, str]] = []
    for transformation in root.iter("TRANSFORMATION"):
        name = transformation.get("NAME", "SIN_NOMBRE")
        for attr in transformation.findall("TABLEATTRIBUTE"):
            if attr.get("NAME") == "Sql Query":
                value = attr.get("VALUE", "").strip()
                if value:
                    results.append((name, value))
    return results


@router.post(
    "/analyze/xml",
    response_model=XmlAnalyzeResponse,
    tags=["Analysis"],
    summary="Analizar consultas SQL desde un archivo XML de Informatica PowerMart",
)
async def analyze_xml(
    request: Request,
    file: UploadFile = File(..., description="Archivo XML de Informatica PowerMart"),
    dialect: str = Form(default="oracle", description="Dialecto SQL: oracle | tsql | postgres | mysql"),
) -> XmlAnalyzeResponse:
    total_start = time.perf_counter()

    mapped_dialect = _DIALECT_MAP.get(dialect.lower().strip())
    if mapped_dialect is None:
        raise HTTPException(
            status_code=422,
            detail=f"Dialecto no soportado: '{dialect}'. Valores válidos: oracle, tsql, postgres, mysql",
        )

    xml_bytes = await file.read()
    if not xml_bytes:
        raise HTTPException(status_code=422, detail="El archivo XML está vacío")

    queries = _extract_queries(xml_bytes)
    if not queries:
        raise HTTPException(
            status_code=422,
            detail="No se encontraron consultas SQL en etiquetas TABLEATTRIBUTE[NAME='Sql Query'] del XML",
        )

    logger.info(
        "XML analyze request received",
        extra={"archivo": file.filename, "dialect": mapped_dialect, "queries_found": len(queries)},
    )

    analysis_service = request.app.state.analysis_service
    consultas: list[ConsultaXmlResult] = []

    for nombre, sql in queries:
        analyze_request = AnalyzeRequest(dialect=mapped_dialect, script=sql)
        result = analysis_service.analyze(analyze_request)
        consultas.append(
            ConsultaXmlResult(
                nombre=nombre,
                dialecto=result.dialecto,
                puntuacion=result.puntuacion,
                criticidad=result.criticidad,
                requiereAprobacion=result.requiereAprobacion,
                problemas=result.problemas,
                estadisticas=result.estadisticas,
                tiempoEjecucionMs=result.tiempoEjecucionMs,
            )
        )

    criticidades = [c.criticidad for c in consultas]
    puntuacion_maxima = max(c.puntuacion for c in consultas)
    consultas_criticas = sum(1 for c in consultas if c.requiereAprobacion)
    total_ms = round((time.perf_counter() - total_start) * 1000, 2)

    logger.info(
        "XML analysis complete",
        extra={
            "total_queries": len(consultas),
            "max_score": puntuacion_maxima,
            "critical_count": consultas_criticas,
            "total_ms": total_ms,
        },
    )

    return XmlAnalyzeResponse(
        exitoso=True,
        totalConsultas=len(consultas),
        criticidadGeneral=_max_criticality(criticidades),
        puntuacionMaxima=puntuacion_maxima,
        consultasCriticas=consultas_criticas,
        requiereAprobacion=consultas_criticas > 0,
        consultas=consultas,
        tiempoTotalMs=total_ms,
    )
