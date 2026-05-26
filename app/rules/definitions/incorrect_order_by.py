from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class IncorrectOrderByRule(BaseRule):
    code = "ORDER_BY_ORDINAL"
    name = "ORDER BY con posición ordinal"
    description = "Detecta ORDER BY usando números de posición en vez de nombres de columna."
    severity = Severity.BAJA
    score = 15

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)
        issues = []
        for stmt in statements:
            for order in stmt.find_all(exp.Order):
                for ordered in order.find_all(exp.Ordered):
                    if isinstance(ordered.this, exp.Literal) and ordered.this.is_number:
                        issues.append(self._issue(
                            message=f"ORDER BY posición ordinal ({ordered.this.this}): frágil ante cambios de columnas en SELECT.",
                            recommendation="Usar nombres de columna explícitos en ORDER BY en lugar de posiciones numéricas.",
                            node=order,
                        ))
        return issues
