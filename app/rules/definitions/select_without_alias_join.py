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
        self._set_script(raw_script)

        # Group by line: keep only the SELECT with the most unaliased columns per line.
        best: dict[object, tuple[int, exp.Expression]] = {}

        for stmt in statements:
            for select in stmt.find_all(exp.Select):
                if not select.find(exp.Join):
                    continue
                unaliased = sum(
                    1 for expr in select.expressions
                    if isinstance(expr, exp.Column) and not expr.alias
                )
                if unaliased <= 3:
                    continue
                line = self._line(select)
                if line not in best or unaliased > best[line][0]:
                    best[line] = (unaliased, select)

        issues = []
        for line_key in sorted(best, key=lambda k: k or 0):
            count, node = best[line_key]
            issues.append(self._issue(
                message=f"{count} columnas sin alias en SELECT con JOINs: ambigüedad en resultado.",
                recommendation="Agregar alias descriptivos a columnas en SELECTs con múltiples tablas para evitar ambigüedad.",
                node=node,
            ))
        return issues
