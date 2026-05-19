from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity

_COMPARISON_OPS = (exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE)

# Oracle/SQL pseudocolumns que normalmente se comparan con literales de forma válida
_SKIP_COLUMNS = {"rownum", "level", "rowid"}


class NoBindVariableRule(BaseRule):
    code = "SIN_BIND_VARIABLE"
    name = "Literal hardcodeado en WHERE sin bind variable"
    description = (
        "Detecta comparaciones con literales directos en WHERE en lugar de bind variables (:var). "
        "En Oracle, cada valor literal distinto genera un nuevo plan de ejecución en el shared pool."
    )
    severity = Severity.BAJA
    score = 10

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            for where in stmt.find_all(exp.Where):
                offending: list[str] = []
                seen: set[str] = set()
                for cmp in where.find_all(_COMPARISON_OPS):
                    col, _ = self._col_literal(cmp)
                    if col is None:
                        continue
                    col_name = col.name.lower()
                    if col_name in _SKIP_COLUMNS or col_name in seen:
                        continue
                    seen.add(col_name)
                    offending.append(col.name)

                if offending:
                    cols = ", ".join(offending[:3])
                    if len(offending) > 3:
                        cols += f" y {len(offending) - 3} más"
                    issues.append(self._issue(
                        message=(
                            f"Literales hardcodeados en WHERE detectados en: {cols}. "
                            "Oracle genera un plan de ejecución distinto por cada valor literal, saturando el shared pool."
                        ),
                        recommendation=(
                            "Reemplazar los valores literales por bind variables. "
                            "Ejemplo: WHERE columna = :v_columna  "
                            "Esto permite a Oracle reutilizar el plan de ejecución y reduce el hard parsing."
                        ),
                    ))
        return issues

    @staticmethod
    def _col_literal(cmp: exp.Expression) -> tuple:
        left, right = cmp.left, cmp.right
        if isinstance(left, exp.Column) and isinstance(right, exp.Literal):
            return left, right
        if isinstance(right, exp.Column) and isinstance(left, exp.Literal):
            return right, left
        return None, None
