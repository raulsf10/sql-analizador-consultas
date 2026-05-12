from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class PivotUnpivotRule(BaseRule):
    code = "USO_PIVOT_UNPIVOT"
    name = "Uso de PIVOT/UNPIVOT complejo"
    description = "Detecta PIVOT/UNPIVOT que puede ser costoso y difícil de mantener."
    severity = Severity.MEDIA
    score = 30

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            if stmt.find(exp.Pivot):
                issues.append(self._issue(
                    message="PIVOT/UNPIVOT detectado: operación costosa que puede ser difícil de escalar.",
                    recommendation="Considerar pivoteo en capa de aplicación para mayor flexibilidad. Si se mantiene en SQL, asegurar índices adecuados.",
                ))
        return issues
