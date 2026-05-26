from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class NotInUsageRule(BaseRule):
    code = "USO_NOT_IN"
    name = "Uso de NOT IN"
    description = "Detecta NOT IN que produce resultados incorrectos cuando la lista contiene NULLs."
    severity = Severity.MEDIA
    score = 20

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)
        issues = []
        for stmt in statements:
            for node in stmt.find_all(exp.Not):
                if node.find(exp.In):
                    issues.append(self._issue(
                        message="Uso de NOT IN: puede producir resultados incorrectos si la lista contiene valores NULL.",
                        recommendation="Reemplazar NOT IN con NOT EXISTS o LEFT JOIN ... WHERE key IS NULL.",
                        node=node,
                    ))
        return issues
