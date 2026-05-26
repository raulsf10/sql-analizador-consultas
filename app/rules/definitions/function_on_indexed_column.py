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

    _COMMON_FUNCS = {
        "upper", "lower", "ltrim", "rtrim", "trim", "convert", "cast",
        "to_char", "to_date", "substr", "substring", "year", "month", "day",
        "datepart", "isnull", "nvl", "coalesce", "len", "length",
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
                    func_name = type(func).__name__.lower()
                    # Check if the function directly wraps a column
                    for arg in func.args.values():
                        if isinstance(arg, exp.Column):
                            issues.append(self._issue(
                                message=f"Función '{func_name}' aplicada a columna en WHERE: deshabilita uso de índices.",
                                recommendation="Mover la función al lado del valor literal o crear un índice basado en función.",
                                node=func,
                            ))
                            break
        return issues
