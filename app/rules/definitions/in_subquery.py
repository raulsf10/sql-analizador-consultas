from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class InSubqueryRule(BaseRule):
    code = "IN_CON_SUBQUERY"
    name = "IN con subquery grande"
    description = "Detecta uso de IN con subqueries que pueden generar planes de ejecución ineficientes."
    severity = Severity.MEDIA
    score = 35

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)
        issues = []
        for stmt in statements:
            for in_expr in stmt.find_all(exp.In):
                if in_expr.find(exp.Subquery):
                    issues.append(self._issue(
                        message="IN con subquery detectado: puede ser ineficiente con grandes volúmenes de datos.",
                        recommendation="Reemplazar IN (SELECT ...) con EXISTS o JOIN para mejor rendimiento.",
                        node=in_expr,
                    ))
        return issues
