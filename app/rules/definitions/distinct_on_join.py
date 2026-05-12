from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class DistinctOnJoinRule(BaseRule):
    code = "DISTINCT_EN_JOIN"
    name = "DISTINCT mal usado sobre JOIN"
    description = "Detecta DISTINCT usado para corregir duplicados causados por JOINs mal definidos."
    severity = Severity.MEDIA
    score = 25

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            for select in stmt.find_all(exp.Select):
                has_distinct = select.args.get("distinct") is not None
                has_join = bool(select.find(exp.Join))
                if has_distinct and has_join:
                    issues.append(self._issue(
                        message="DISTINCT sobre consulta con JOIN: posible señal de cardinalidad incorrecta en el JOIN.",
                        recommendation="Revisar condiciones del JOIN para eliminar duplicados en origen en vez de usar DISTINCT.",
                    ))
        return issues
