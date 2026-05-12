import time
from app.models.request_models import AnalyzeRequest
from app.models.response_models import AnalyzeResponse, Issue
from app.rules.rule_manager import RuleManager
from app.analyzers.sql_analyzer import SQLAnalyzer
from app.services.risk_scoring_service import RiskScoringService
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AnalysisService:

    def __init__(
        self,
        rule_manager: RuleManager,
        sql_analyzer: SQLAnalyzer,
        scoring_service: RiskScoringService,
        approval_threshold: int = 60,
    ) -> None:
        self._rules = rule_manager
        self._analyzer = sql_analyzer
        self._scoring = scoring_service
        self._approval_threshold = approval_threshold

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        start = time.perf_counter()

        statements = self._analyzer.parse(request.script, request.dialect)

        issues: list[Issue] = []
        for rule in self._rules.get_all():
            try:
                found = rule.analyze(statements, request.script)
                issues.extend(found)
            except Exception as exc:
                logger.warning(f"Rule '{rule.code}' raised an exception: {exc}", exc_info=True)

        score = self._scoring.calculate_score(issues)
        criticality = self._scoring.get_criticality(score)
        requires_approval = self._scoring.requires_approval(score, self._approval_threshold)
        statistics = self._analyzer.extract_statistics(statements)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "Analysis complete",
            extra={
                "dialect": request.dialect,
                "score": score,
                "criticality": criticality.value,
                "execution_time_ms": elapsed_ms,
                "issues_found": len(issues),
            },
        )

        return AnalyzeResponse(
            exitoso=True,
            criticidad=criticality,
            puntuacion=score,
            requiereAprobacion=requires_approval,
            problemas=issues,
            estadisticas=statistics,
            dialecto=request.dialect,
            tiempoEjecucionMs=elapsed_ms,
        )
