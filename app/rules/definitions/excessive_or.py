from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity

_OR_THRESHOLD = 5


class ExcessiveOrRule(BaseRule):
    code = "OR_EXCESIVO"
    name = "Uso excesivo de OR en WHERE"
    description = f"Detecta más de {_OR_THRESHOLD} condiciones OR que pueden degradar el plan de ejecución."
    severity = Severity.MEDIA
    score = 25

    def _count_or(self, node: exp.Expression) -> int:
        if isinstance(node, exp.Or):
            return 1 + self._count_or(node.left) + self._count_or(node.right)
        return 0

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            for where in stmt.find_all(exp.Where):
                or_count = self._count_or(where.this)
                if or_count >= _OR_THRESHOLD:
                    issues.append(self._issue(
                        message=f"Exceso de condiciones OR ({or_count}) en WHERE: puede impedir uso eficiente de índices.",
                        recommendation="Reemplazar múltiples OR con IN (...) o usar UNION ALL de queries más simples.",
                    ))
        return issues
