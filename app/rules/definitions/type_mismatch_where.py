from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


_ID_COLUMN_HINTS = {"id", "code", "codigo", "num", "number", "clave", "key"}


class TypeMismatchWhereRule(BaseRule):
    code = "TIPO_INCOMPATIBLE_WHERE"
    name = "Comparación de tipos distintos en WHERE"
    description = "Detecta comparaciones donde una columna numérica se compara con un literal de texto."
    severity = Severity.MEDIA
    score = 25

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)
        issues = []
        for stmt in statements:
            for where in stmt.find_all(exp.Where):
                for cmp in where.find_all((exp.EQ, exp.NEQ)):
                    col, lit = None, None
                    if isinstance(cmp.left, exp.Column) and isinstance(cmp.right, exp.Literal):
                        col, lit = cmp.left, cmp.right
                    elif isinstance(cmp.right, exp.Column) and isinstance(cmp.left, exp.Literal):
                        col, lit = cmp.right, cmp.left
                    if col and lit and lit.is_string:
                        col_name = col.name.lower()
                        if any(hint in col_name for hint in _ID_COLUMN_HINTS):
                            # Column name suggests numeric but compared to string
                            if lit.this.isdigit() is False and not lit.this.replace(".", "").isdigit():
                                issues.append(self._issue(
                                    message=f"Posible comparación de tipo incorrecto: columna '{col.name}' (numérica) comparada con literal texto '{lit.this}'.",
                                    recommendation="Verificar tipos de datos y usar casteo explícito: CAST(col AS VARCHAR) = '...' o col = CAST('...' AS INT).",
                                    node=cmp,
                                ))
        return issues
