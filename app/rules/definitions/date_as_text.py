from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity
import re


_DATE_PATTERN = re.compile(
    r"^\d{4}[-/]\d{2}[-/]\d{2}$|^\d{2}[-/]\d{2}[-/]\d{4}$|^\d{8}$"
)

_DATE_COLUMN_HINTS = {"fecha", "date", "dt", "fch", "timestamp", "created", "updated", "modified"}


class DateAsTextRule(BaseRule):
    code = "FECHA_COMO_TEXTO"
    name = "Comparación de fechas como texto"
    description = "Detecta comparaciones de columnas de fecha con literales de texto que pueden causar errores de conversión."
    severity = Severity.MEDIA
    score = 30

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            for cmp in stmt.find_all((exp.EQ, exp.GT, exp.LT, exp.GTE, exp.LTE)):
                for side in (cmp.left, cmp.right):
                    if not isinstance(side, exp.Literal) or not side.is_string:
                        continue
                    val = side.this
                    if not _DATE_PATTERN.match(val):
                        continue
                    # Check if the other side is a column with a date-like name
                    other = cmp.right if side is cmp.left else cmp.left
                    if isinstance(other, exp.Column):
                        col_name = other.name.lower()
                        if any(hint in col_name for hint in _DATE_COLUMN_HINTS):
                            issues.append(self._issue(
                                message=f"Comparación de fecha como texto '{val}' sobre columna '{other.name}': puede causar conversión implícita.",
                                recommendation="Usar funciones de fecha explícitas: TO_DATE('...', 'YYYY-MM-DD') en Oracle, CAST('...' AS DATE) en SQL Server.",
                            ))
        return issues
