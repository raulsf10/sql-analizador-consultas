from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class CalculatedColumnFilterRule(BaseRule):
    code = "FILTRO_COLUMNA_CALCULADA"
    name = "Filtro sobre columna calculada"
    description = "Detecta filtros WHERE sobre expresiones calculadas que impiden uso de índices."
    severity = Severity.MEDIA
    score = 30

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            for where in stmt.find_all(exp.Where):
                for cmp in where.find_all((exp.EQ, exp.GT, exp.LT, exp.GTE, exp.LTE, exp.NEQ)):
                    for side in (cmp.left, cmp.right):
                        if isinstance(side, (exp.Add, exp.Sub, exp.Mul, exp.Div)):
                            issues.append(self._issue(
                                message="Filtro WHERE sobre expresión aritmética: no puede usar índices de columna.",
                                recommendation="Mover el cálculo al lado del literal o usar columnas calculadas persistidas/indexadas.",
                            ))
                            break
        return issues
