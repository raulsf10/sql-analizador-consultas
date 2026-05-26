from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


def _unwrap(expr: exp.Expression) -> exp.Expression:
    while isinstance(expr, exp.Paren):
        expr = expr.this
    return expr


def _is_tautological(expr: exp.Expression) -> bool:
    expr = _unwrap(expr)

    if isinstance(expr, exp.Boolean) and expr.this is True:
        return True

    if isinstance(expr, exp.EQ):
        left = _unwrap(expr.left)
        right = _unwrap(expr.right)
        if isinstance(left, exp.Literal) and isinstance(right, exp.Literal):
            return left.this == right.this

    if isinstance(expr, exp.And):
        return _is_tautological(expr.left) and _is_tautological(expr.right)

    if isinstance(expr, exp.Or):
        return _is_tautological(expr.left) or _is_tautological(expr.right)

    return False


class TautologicalWhereRule(BaseRule):
    code = "WHERE_SIEMPRE_VERDADERO"
    name = "WHERE siempre verdadero"
    description = "Detecta WHERE con condición siempre verdadera (1=1, TRUE, 'a'='a'), equivalente a operar sin filtro."
    severity = Severity.CRITICA
    score = 100

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)
        issues = []
        for stmt in statements:
            if isinstance(stmt, exp.Delete):
                where = stmt.find(exp.Where)
                if where and _is_tautological(where.this):
                    issues.append(Issue(
                        codigo=self.code,
                        severidad=Severity.CRITICA,
                        mensaje="DELETE con WHERE siempre verdadero: eliminará TODOS los registros de la tabla.",
                        linea=self._line(where),
                        recomendacion="La condición WHERE no filtra registros. Reemplazarla por un filtro real (ej: WHERE id = :id).",
                        puntuacion=100,
                    ))
            elif isinstance(stmt, exp.Update):
                where = stmt.find(exp.Where)
                if where and _is_tautological(where.this):
                    issues.append(Issue(
                        codigo=self.code,
                        severidad=Severity.CRITICA,
                        mensaje="UPDATE con WHERE siempre verdadero: modificará TODOS los registros de la tabla.",
                        linea=self._line(where),
                        recomendacion="La condición WHERE no filtra registros. Reemplazarla por un filtro real (ej: WHERE id = :id).",
                        puntuacion=90,
                    ))
        return issues
