from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class DeleteWithoutWhereRule(BaseRule):
    code = "DELETE_SIN_WHERE"
    name = "DELETE sin cláusula WHERE"
    description = "Detecta sentencias DELETE sin WHERE que eliminan todos los registros de la tabla."
    severity = Severity.CRITICA
    score = 100

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            for delete in stmt.find_all(exp.Delete):
                if not delete.find(exp.Where):
                    issues.append(self._issue(
                        message="DELETE sin cláusula WHERE: eliminará TODOS los registros de la tabla.",
                        recommendation="Agregar cláusula WHERE. Ejemplo: DELETE FROM tabla WHERE id = :id",
                    ))
        return issues
