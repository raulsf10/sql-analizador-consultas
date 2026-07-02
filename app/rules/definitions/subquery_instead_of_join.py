from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity

_SUBQUERY_THRESHOLD = 2


class SubqueryInsteadOfJoinRule(BaseRule):
    code = "SUBQUERY_EN_VEZ_DE_JOIN"
    name = "Subqueries en FROM en lugar de JOINs"
    description = "Detecta múltiples subqueries en FROM que deberían ser JOINs ANSI."
    severity = Severity.MEDIA
    score = 30

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)

        # For each line, keep only the SELECT with the highest subquery count.
        # Multiple nested SELECTs often resolve to the same line; reporting the
        # worst one per line avoids flooding the report with duplicate entries.
        best: dict[object, tuple[int, exp.Expression]] = {}

        for stmt in statements:
            for select in stmt.find_all(exp.Select):
                from_clause = select.find(exp.From)
                if not from_clause:
                    continue
                subq_count = len(list(from_clause.find_all(exp.Subquery)))
                if subq_count < _SUBQUERY_THRESHOLD:
                    continue
                line = self._line(select)
                if line not in best or subq_count > best[line][0]:
                    best[line] = (subq_count, select)

        issues = []
        for line_key in sorted(best, key=lambda k: k or 0):
            count, node = best[line_key]
            issues.append(self._issue(
                message=f"{count} subqueries en cláusula FROM: patrón ineficiente versus JOINs ANSI.",
                recommendation="Reemplazar subqueries derivadas en FROM con JOINs explícitos o CTEs para mejor legibilidad y rendimiento.",
                node=node,
            ))
        return issues
