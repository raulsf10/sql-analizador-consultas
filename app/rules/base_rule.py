from abc import ABC, abstractmethod
from typing import List, Optional
import sqlglot
from app.models.response_models import Issue, Severity


class BaseRule(ABC):
    code: str = ""
    name: str = ""
    description: str = ""
    severity: Severity = Severity.BAJA
    score: int = 0

    @abstractmethod
    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        """Analyze parsed AST statements and return a list of issues found."""

    def _issue(self, message: str, recommendation: str, line: Optional[int] = None) -> Issue:
        return Issue(
            codigo=self.code,
            severidad=self.severity,
            mensaje=message,
            linea=line,
            recomendacion=recommendation,
            puntuacion=self.score,
        )
