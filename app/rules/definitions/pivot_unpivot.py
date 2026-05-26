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
        self._set_script(raw_script)
        issues = []
        for stmt in statements:
            pivot = stmt.find(exp.Pivot)
            if pivot:
                issues.append(self._issue(
                    message="PIVOT/UNPIVOT detectado: operación costosa que puede ser difícil de escalar.",
                    recommendation="Considerar pivoteo en capa de aplicación para mayor flexibilidad. Si se mantiene en SQL, asegurar índices adecuados.",
                    node=pivot,
                ))
        return issues
