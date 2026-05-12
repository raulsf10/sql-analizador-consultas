from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class SelectWithoutAliasJoinRule(BaseRule):
    code = "SELECT_SIN_ALIAS_JOIN"
    name = "SELECT sin alias de columna en JOIN múltiple"
    description = "Detecta columnas en SELECT sin alias cuando hay múltiples tablas en JOINs."
    severity = Severity.BAJA
    score = 10

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            for select in stmt.find_all(exp.Select):
                if not select.find(exp.Join):
                    continue
                unaliased = []
                for expr in select.expressions:
                    if isinstance(expr, exp.Column) and not expr.alias:
                        unaliased.append(expr.name)
                if len(unaliased) > 3:
                    issues.append(self._issue(
                        message=f"{len(unaliased)} columnas sin alias en SELECT con JOINs: ambigüedad en resultado.",
                        recommendation="Agregar alias descriptivos a columnas en SELECTs con múltiples tablas para evitar ambigüedad.",
                    ))
        return issues
