import time
import xml.etree.ElementTree as ET
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from typing import Optional
from app.models.request_models import AnalyzeRequest, _DIALECT_MAP
from app.db import catalog_repository
from app.models.response_models import (
    ConsultaXmlResult,
    XmlAnalyzeResponse,
    Criticality,
    Issue,
    Severity,
)
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

_DEFAULT_DIALECT = "oracle"

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


def _resolve_dialect(dialect_raw: str) -> str:
    """Map a PowerMart DATABASETYPE string to an internal dialect key."""
    return _DIALECT_MAP.get(dialect_raw.lower().strip(), _DEFAULT_DIALECT)


def _extract_queries(xml_bytes: bytes) -> list[tuple[str, str, str]]:
    """Return list of (transformation_name, sql_query, dialect) from PowerMart XML.

    Dialect is resolved from the SOURCE element associated with each Source
    Qualifier via the ASSOCIATED_SOURCE_INSTANCE chain in the MAPPING.
    Falls back to _DEFAULT_DIALECT when the chain cannot be resolved.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise HTTPException(status_code=422, detail=f"XML inválido: {exc}")

    # Build SOURCE name → DATABASETYPE from all SOURCE elements in the document
    source_db: dict[str, str] = {
        s.get("NAME", ""): s.get("DATABASETYPE", "")
        for s in root.iter("SOURCE")
        if s.get("NAME")
    }

    results: list[tuple[str, str, str]] = []

    for mapping in root.iter("MAPPING"):
        # SQ instance name → list of associated source instance names
        sq_to_sources: dict[str, list[str]] = {}
        for instance in mapping.findall("INSTANCE"):
            if instance.get("TRANSFORMATION_TYPE") == "Source Qualifier":
                sq_name = instance.get("NAME", "")
                sq_to_sources[sq_name] = [
                    a.get("NAME", "")
                    for a in instance.findall("ASSOCIATED_SOURCE_INSTANCE")
                ]

        # Source instance name → SOURCE definition name (== SOURCE NAME in source_db)
        source_instance_to_def: dict[str, str] = {
            inst.get("NAME", ""): inst.get("TRANSFORMATION_NAME", "")
            for inst in mapping.findall("INSTANCE")
            if inst.get("TYPE") == "SOURCE"
        }

        for transformation in mapping.findall("TRANSFORMATION"):
            name = transformation.get("NAME", "SIN_NOMBRE")

            sql = ""
            for attr in transformation.findall("TABLEATTRIBUTE"):
                if attr.get("NAME") == "Sql Query":
                    sql = attr.get("VALUE", "").strip()
                    break
            if not sql:
                continue

            # Walk: SQ → ASSOCIATED_SOURCE_INSTANCE → SOURCE instance → SOURCE element
            dialect_raw = ""
            for src_inst_name in sq_to_sources.get(name, []):
                src_def_name = source_instance_to_def.get(src_inst_name, "")
                db_type = source_db.get(src_def_name, "")
                if db_type:
                    dialect_raw = db_type
                    break

            # Fallback: use the first SOURCE found in this mapping
            if not dialect_raw:
                for src_def_name in source_instance_to_def.values():
                    db_type = source_db.get(src_def_name, "")
                    if db_type:
                        dialect_raw = db_type
                        break

            results.append((name, sql, dialect_raw))

    return results


@router.post(
    "/analyze/xml",
    response_model=XmlAnalyzeResponse,
    tags=["Analysis"],
    summary=" ",
)
async def analyze_xml(
    request: Request,
    file: UploadFile = File(..., description="Archivo XML de Informatica PowerMart"),
    ruta: Optional[str] = Form(default=None, description="Nombre o ruta del workflow en PowerCenter (ej: WF_CATALOGOS_MAESTROS)"),
) -> XmlAnalyzeResponse:
    total_start = time.perf_counter()

    xml_bytes = await file.read()
    if not xml_bytes:
        raise HTTPException(status_code=422, detail="El archivo XML está vacío")

    queries = _extract_queries(xml_bytes)
    if not queries:
        raise HTTPException(
            status_code=422,
            detail="No se encontraron consultas SQL en etiquetas TABLEATTRIBUTE[NAME='Sql Query'] del XML",
        )

    wf_match = catalog_repository.find_critical_wf(ruta) if ruta else None

    logger.info(
        "XML analyze request received",
        extra={
            "archivo": file.filename,
            "ruta": ruta,
            "ruta_critica": wf_match is not None,
            "queries_found": len(queries),
        },
    )

    analysis_service = request.app.state.analysis_service
    consultas: list[ConsultaXmlResult] = []

    for nombre, sql, dialect_raw in queries:
        mapped_dialect = _resolve_dialect(dialect_raw)
        if dialect_raw and mapped_dialect == _DEFAULT_DIALECT and dialect_raw.lower() != _DEFAULT_DIALECT:
            logger.warning(
                "Unrecognized DATABASETYPE in XML, falling back to default dialect",
                extra={"transformation": nombre, "databasetype": dialect_raw, "fallback": _DEFAULT_DIALECT},
            )

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

    total_ms = round((time.perf_counter() - total_start) * 1000, 2)

    # If the ruta matches a critical WF, force overall criticality to CRITICA
    if wf_match:
        ruta_issue = Issue(
            codigo="RUTA_CRITICA",
            severidad=Severity.CRITICA,
            mensaje=f"El workflow '{wf_match}' está catalogado como crítico",
            recomendacion="Esta consulta pertenece a un workflow crítico. Requiere revisión y aprobación especial antes de su ejecución.",
            puntuacion=100,
        )
        for consulta in consultas:
            consulta.problemas.append(ruta_issue)
            consulta.criticidad = Criticality.CRITICA
            consulta.requiereAprobacion = True
            consulta.puntuacion = 100

    criticidades = [c.criticidad for c in consultas]
    puntuacion_maxima = max(c.puntuacion for c in consultas)
    consultas_criticas = sum(1 for c in consultas if c.requiereAprobacion)
    criticidad_general = _max_criticality(criticidades)
    requiere_aprobacion = consultas_criticas > 0

    logger.info(
        "XML analysis complete",
        extra={
            "total_queries": len(consultas),
            "max_score": puntuacion_maxima,
            "critical_count": consultas_criticas,
            "ruta_critica": wf_match,
            "total_ms": total_ms,
        },
    )

    return XmlAnalyzeResponse(
        exitoso=True,
        totalConsultas=len(consultas),
        criticidadGeneral=criticidad_general,
        puntuacionMaxima=puntuacion_maxima,
        consultasCriticas=consultas_criticas,
        requiereAprobacion=requiere_aprobacion,
        rutaCritica=wf_match is not None,
        rutaCoincidencia=wf_match,
        consultas=consultas,
        tiempoTotalMs=total_ms,
    )
