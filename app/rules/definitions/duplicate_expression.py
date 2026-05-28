import re
from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity

_MIN_REPETITIONS = 3
_CASE_MIN_LEN = 20
_EXPR_MIN_LEN = 35
# Structural similarity: min chars after normalization AND min members in group
_STRUCT_MIN_LEN = 50
_STRUCT_MIN_REPETITIONS = 3

_LITERAL_RE = re.compile(r"'[^']*'")
_NUMBER_RE = re.compile(r"(?<![A-Za-z_0-9.])\d+(?:\.\d+)?(?![A-Za-z_0-9])")


def _normalize(sql: str) -> str:
    """Replace all literal values with ? to expose structural template."""
    s = _LITERAL_RE.sub("'?'", sql)
    s = _NUMBER_RE.sub("?", s)
    return s


class DuplicateExpressionRule(BaseRule):
    code = "EXPRESION_REPETIDA"
    name = "Expresión compleja duplicada"
    description = (
        "Detecta bloques CASE idénticos o estructuralmente similares repetidos 3 o más veces. "
        "La repetición indica lógica que debería extraerse a una función SQL o CTE."
    )
    severity = Severity.BAJA
    score = 15

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)
        issues = []

        # ── Pass 1: exact duplicates (accumulate across all statements) ──────
        exact_counts: dict[str, int] = {}
        exact_first: dict[str, exp.Expression] = {}

        for stmt in statements:
            for node in stmt.find_all(exp.Case):
                try:
                    sql = node.sql(dialect="oracle").strip()
                except Exception:
                    continue
                if len(sql) < _CASE_MIN_LEN:
                    continue
                if sql not in exact_first:
                    exact_first[sql] = node
                exact_counts[sql] = exact_counts.get(sql, 0) + 1

            for node in stmt.find_all((exp.Add, exp.Sub, exp.Mul, exp.Div)):
                try:
                    sql = node.sql(dialect="oracle").strip()
                except Exception:
                    continue
                if len(sql) < _EXPR_MIN_LEN:
                    continue
                if sql not in exact_first:
                    exact_first[sql] = node
                exact_counts[sql] = exact_counts.get(sql, 0) + 1

        reported_exact: set[str] = set()
        for sql, count in sorted(exact_counts.items(), key=lambda x: -len(x[0])):
            if count < _MIN_REPETITIONS:
                continue
            reported_exact.add(sql)
            display = sql[:80] + "..." if len(sql) > 80 else sql
            issues.append(self._issue(
                message=f"Expresión idéntica repetida {count} veces: {display}",
                recommendation=(
                    "Extraer la expresión a un CTE (WITH nombre AS (...)) o a una función "
                    "almacenada para eliminar la repetición y facilitar el mantenimiento."
                ),
                node=exact_first[sql],
            ))

        # ── Pass 2: structural similarity (accumulate across all statements) ─
        struct_counts: dict[str, int] = {}
        struct_first: dict[str, exp.Expression] = {}
        struct_example: dict[str, str] = {}

        for stmt in statements:
            for node in stmt.find_all(exp.Case):
                try:
                    sql = node.sql(dialect="oracle").strip()
                except Exception:
                    continue
                if len(sql) < _STRUCT_MIN_LEN:
                    continue
                if sql in reported_exact:
                    continue
                norm = _normalize(sql)
                if norm not in struct_first:
                    struct_first[norm] = node
                    struct_example[norm] = sql
                struct_counts[norm] = struct_counts.get(norm, 0) + 1

        for norm, count in sorted(struct_counts.items(), key=lambda x: -x[1]):
            if count < _STRUCT_MIN_REPETITIONS:
                continue
            example = struct_example[norm]
            display = example[:80] + "..." if len(example) > 80 else example
            issues.append(self._issue(
                message=(
                    f"Bloque CASE con estructura similar repetido {count} veces "
                    f"(misma lógica, distintos valores): {display}"
                ),
                recommendation=(
                    "La lógica se repite con pequeñas variaciones en los valores literales. "
                    "Crear una función SQL almacenada que reciba los parámetros variables "
                    "eliminaría la duplicación y haría el código más mantenible."
                ),
                node=struct_first[norm],
            ))

        return issues
