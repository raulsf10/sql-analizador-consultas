from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class TruncateTableRule(BaseRule):
    code = "TRUNCATE_TABLA"
    name = "TRUNCATE TABLE: vaciar tabla"
    description = "Detecta TRUNCATE TABLE que elimina todos los registros sin posibilidad de rollback en algunos motores."
    severity = Severity.CRITICA
    score = 100

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            if stmt.find(exp.TruncateTable):
                issues.append(self._issue(
                    message="TRUNCATE TABLE detectado: elimina TODOS los registros y puede no ser reversible.",
                    recommendation="Verificar que existe un respaldo reciente. Considerar DELETE con WHERE en ambientes productivos.",
                ))
        return issues
