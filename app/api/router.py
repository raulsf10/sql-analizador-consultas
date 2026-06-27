from fastapi import APIRouter
from app.api.endpoints import analyze, analyze_xml, catalog

api_router = APIRouter()
api_router.include_router(analyze.router)
api_router.include_router(analyze_xml.router)
api_router.include_router(catalog.router)
