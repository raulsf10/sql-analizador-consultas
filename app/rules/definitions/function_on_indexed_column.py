from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class FunctionOnIndexedColumnRule(BaseRule):
    code = "FUNCION_SOBRE_COLUMNA"
    name = "Función sobre columna en WHERE"
    description = (
        "Detecta cualquier función aplicada directamente a una columna en WHERE. "
        "Envolver una columna en una función impide que el motor use el índice de esa columna."
    )
    severity = Severity.ALTA
    score = 45

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)
        issues = []
        for stmt in statements:
            for select in stmt.find_all(exp.Select):
                where = select.find(exp.Where)
                if not where:
                    continue
                for func in where.find_all(exp.Func):
                    if isinstance(func, exp.AggFunc):
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
                            recommendation=(
                                "Mover la función al lado del valor literal o crear un índice basado en función. "
                                "Ejemplo: en lugar de WHERE UPPER(nombre) = 'JUAN', "
                                "usar WHERE nombre = 'JUAN' o crear un índice funcional."
                            ),
                            node=func,
                        ))
        return issues
