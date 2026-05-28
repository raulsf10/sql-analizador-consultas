from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class FunctionOnIndexedColumnRule(BaseRule):
    code = "FUNCION_SOBRE_COLUMNA"
    name = "Función sobre columna en WHERE"
    description = "Detecta funciones aplicadas a columnas en WHERE que impiden el uso de índices."
    severity = Severity.ALTA
    score = 45

    # SQLGlot class names (lowercase) for functions that disable index usage.
    # Includes both direct class names and mapped names (e.g. TO_DATE → StrToDate).
    _COMMON_FUNCS = {
        # Class names that match the SQL function name directly
        "upper", "lower", "trim", "length", "coalesce", "cast",
        "year", "month", "day",
        # SQLGlot internal class names for Oracle/SQL Server functions
        "strtodate",    # TO_DATE
        "tochar",       # TO_CHAR
        # Anonymous functions — matched via func.name
        "ltrim", "rtrim", "substr", "substring",
        "isnull", "nvl", "convert", "datepart", "len",
    }

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)
        issues = []
        for stmt in statements:
            for select in stmt.find_all(exp.Select):
                where = select.find(exp.Where)
                if not where:
                    continue
                for func in where.find_all(exp.Func):
                    cls_name = type(func).__name__.lower()
                    # Anonymous keeps the original SQL name in func.name
                    func_name = func.name.lower() if cls_name == "anonymous" else cls_name
                    if func_name not in self._COMMON_FUNCS:
                        continue
                    col_found = False
                    for arg in func.args.values():
                        targets = arg if isinstance(arg, list) else [arg]
                        if any(isinstance(t, exp.Column) for t in targets):
                            col_found = True
                            break
                    if col_found:
                        display = func.sql(dialect="oracle").split("(")[0].strip()
                        issues.append(self._issue(
                            message=f"Función '{display}' aplicada a columna en WHERE: deshabilita uso de índices.",
                            recommendation="Mover la función al lado del valor literal o crear un índice basado en función.",
                            node=func,
                        ))
        return issues
