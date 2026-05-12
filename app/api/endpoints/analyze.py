from fastapi import APIRouter, Request
from app.models.request_models import AnalyzeRequest
from app.models.response_models import AnalyzeResponse
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    tags=["Analysis"],
)
async def analyze_sql(payload: AnalyzeRequest, request: Request) -> AnalyzeResponse:
    analysis_service = request.app.state.analysis_service
    logger.info(
        "Analyze request received",
        extra={"endpoint": "/analyze", "dialect": payload.dialect},
    )
    return analysis_service.analyze(payload)
