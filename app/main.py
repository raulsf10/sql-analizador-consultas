from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config.settings import settings
from app.core.exceptions import (
    SQLParseException,
    InvalidDialectException,
    sql_parse_exception_handler,
    invalid_dialect_exception_handler,
    global_exception_handler,
)
from app.core.logging_config import setup_logging, get_logger
from app.rules.registry import build_rule_manager
from app.analyzers.sql_analyzer import SQLAnalyzer
from app.services.risk_scoring_service import RiskScoringService
from app.services.analysis_service import AnalysisService
from app.db.database import init_db
from app.db import catalog_repository

setup_logging(log_level=settings.log_level, log_file=settings.log_file)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(f"Starting {settings.app_name} v{settings.app_version} [{settings.app_env}]")

    init_db(settings.database_url)
    catalog_repository.load_catalog(settings.database_url)
    logger.info(
        "Catalog loaded",
        extra={
            "tablas_criticas": len(catalog_repository.get_critical_tables()),
            "wf_criticos": len(catalog_repository.get_critical_wfs()),
        },
    )

    rule_manager = build_rule_manager()
    sql_analyzer = SQLAnalyzer()
    scoring_service = RiskScoringService()
    analysis_service = AnalysisService(
        rule_manager=rule_manager,
        sql_analyzer=sql_analyzer,
        scoring_service=scoring_service,
        approval_threshold=settings.approval_threshold,
    )

    app.state.settings = settings
    app.state.rule_manager = rule_manager
    app.state.analysis_service = analysis_service

    logger.info(f"Rule engine initialized with {len(rule_manager.get_all())} rules")
    yield
    logger.info(f"{settings.app_name} shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="SQL Analizador consultas",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(SQLParseException, sql_parse_exception_handler)
    app.add_exception_handler(InvalidDialectException, invalid_dialect_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    app.include_router(api_router)

    return app


app = create_app()
