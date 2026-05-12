from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class CteReuseRule(BaseRule):
    code = "REUTILIZACION_CTE"
    name = "Reutilización incorrecta de CTE"
    description = "Detecta CTEs definidos pero no usados, o CTEs usados múltiples veces sin materialización."
    severity = Severity.BAJA
    score = 15

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            with_clause = stmt.find(exp.With)
            if not with_clause:
                continue
            for cte in with_clause.find_all(exp.CTE):
                cte_name = cte.alias.lower() if cte.alias else ""
                if not cte_name:
                    continue
                # Count references to CTE name in the rest of the statement
                count = sum(
                    1 for table in stmt.find_all(exp.Table)
                    if table.name.lower() == cte_name and table is not cte.find(exp.Table)
                )
                if count == 0:
                    issues.append(self._issue(
                        message=f"CTE '{cte.alias}' definido pero nunca referenciado: código muerto.",
                        recommendation="Eliminar CTEs no utilizados para mejorar legibilidad y rendimiento.",
                    ))
                elif count > 2:
                    issues.append(self._issue(
                        message=f"CTE '{cte.alias}' referenciado {count} veces: puede causar re-evaluación en algunos motores.",
                        recommendation="Considerar tablas temporales o materialización explícita si el CTE es costoso.",
                    ))
        return issues
