from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class SelectStarRule(BaseRule):
    code = "SELECT_ASTERISCO"
    name = "Uso de SELECT *"
    description = "Detecta uso de SELECT * que trae columnas innecesarias y rompe contratos de interfaz."
    severity = Severity.BAJA
    score = 20

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)
        issues = []
        for stmt in statements:
            for select in stmt.find_all(exp.Select):
                for expr in select.expressions:
                    if isinstance(expr, exp.Star):
                        issues.append(self._issue(
                            message="Uso de SELECT *: trae todas las columnas incluyendo innecesarias.",
                            recommendation="Especificar explícitamente las columnas requeridas. Ejemplo: SELECT id, nombre, fecha FROM tabla",
                            node=select,
                        ))
                        break
        return issues
