import re
from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity

_SUBQUERY_MIN_REPETITIONS = 2   # 2+ es suficiente para ser un problema
_MIN_REPETITIONS = 3
_SUBQUERY_MIN_LEN = 20
_CASE_MIN_LEN = 20
_EXPR_MIN_LEN = 35
_STRUCT_MIN_LEN = 50
_STRUCT_MIN_REPETITIONS = 3

_LITERAL_RE = re.compile(r"'[^']*'")
_NUMBER_RE = re.compile(r"(?<![A-Za-z_0-9.])\d+(?:\.\d+)?(?![A-Za-z_0-9])")


def _normalize(sql: str) -> str:
    s = _LITERAL_RE.sub("'?'", sql)
    s = _NUMBER_RE.sub("?", s)
    return s


class DuplicateExpressionRule(BaseRule):
    code = "EXPRESION_REPETIDA"
    name = "Subconsulta o expresión duplicada"
    description = (
        "Detecta subconsultas escalares idénticas repetidas 2 o más veces, "
        "bloques CASE idénticos o estructuralmente similares repetidos 3 o más veces, "
        "y expresiones aritméticas idénticas repetidas 3 o más veces. "
        "La repetición fuerza al motor a ejecutar la misma lógica múltiples veces."
    )
    severity = Severity.BAJA
    score = 15

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)
        issues = []
        reported_sqls: set[str] = set()

        # ── Pass 1: subconsultas escalares idénticas (threshold: 2+) ─────────
        subquery_counts: dict[str, int] = {}
        subquery_first: dict[str, exp.Expression] = {}

        for stmt in statements:
            for node in stmt.find_all(exp.Subquery):
                try:
                    sql = node.sql(dialect="oracle").strip()
                except Exception:
                    continue
                if len(sql) < _SUBQUERY_MIN_LEN:
                    continue
                if sql not in subquery_first:
                    subquery_first[sql] = node
                subquery_counts[sql] = subquery_counts.get(sql, 0) + 1

        for sql, count in sorted(subquery_counts.items(), key=lambda x: -len(x[0])):
            if count < _SUBQUERY_MIN_REPETITIONS:
                continue
            reported_sqls.add(sql)
            display = sql[:120] + "..." if len(sql) > 120 else sql
            issues.append(self._issue(
                message=f"Subconsulta idéntica ejecutada {count} veces: {display}",
                recommendation=(
                    "Extraer la subconsulta a un CTE (WITH nombre AS (...)) para que el motor "
                    "la calcule una sola vez. Cada repetición fuerza una ejecución independiente."
                ),
                node=subquery_first[sql],
            ))

        # ── Pass 2: expresiones exactas — CASE y aritmética (threshold: 3+) ──
        exact_counts: dict[str, int] = {}
        exact_first: dict[str, exp.Expression] = {}

        for stmt in statements:
            for node in stmt.find_all(exp.Case):
                try:
                    sql = node.sql(dialect="oracle").strip()
                except Exception:
                    continue
                if len(sql) < _CASE_MIN_LEN or sql in reported_sqls:
                    continue
                if sql not in exact_first:
                    exact_first[sql] = node
                exact_counts[sql] = exact_counts.get(sql, 0) + 1

            for node in stmt.find_all((exp.Add, exp.Sub, exp.Mul, exp.Div)):
                try:
                    sql = node.sql(dialect="oracle").strip()
                except Exception:
                    continue
                if len(sql) < _EXPR_MIN_LEN or sql in reported_sqls:
                    continue
                if sql not in exact_first:
                    exact_first[sql] = node
                exact_counts[sql] = exact_counts.get(sql, 0) + 1

        reported_exact: set[str] = set()
        for sql, count in sorted(exact_counts.items(), key=lambda x: -len(x[0])):
            if count < _MIN_REPETITIONS:
                continue
            reported_exact.add(sql)
            reported_sqls.add(sql)
            display = sql[:80] + "..." if len(sql) > 80 else sql
            issues.append(self._issue(
                message=f"Expresión idéntica repetida {count} veces: {display}",
                recommendation=(
                    "Extraer la expresión a un CTE (WITH nombre AS (...)) o a una función "
                    "almacenada para eliminar la repetición y facilitar el mantenimiento."
                ),
                node=exact_first[sql],
            ))

        # ── Pass 3: similitud estructural — CASE (threshold: 3+) ─────────────
        struct_counts: dict[str, int] = {}
        struct_first: dict[str, exp.Expression] = {}
        struct_example: dict[str, str] = {}

        for stmt in statements:
            for node in stmt.find_all(exp.Case):
                try:
                    sql = node.sql(dialect="oracle").strip()
                except Exception:
                    continue
                if len(sql) < _STRUCT_MIN_LEN or sql in reported_sqls:
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
