from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class UpdateWithoutWhereRule(BaseRule):
    code = "UPDATE_SIN_WHERE"
    name = "UPDATE sin cláusula WHERE"
    description = "Detecta sentencias UPDATE sin WHERE que modifican todos los registros de la tabla."
    severity = Severity.CRITICA
    score = 90

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            for update in stmt.find_all(exp.Update):
                if not update.find(exp.Where):
                    issues.append(self._issue(
                        message="UPDATE sin cláusula WHERE: modificará TODOS los registros de la tabla.",
                        recommendation="Agregar cláusula WHERE. Ejemplo: UPDATE tabla SET col = val WHERE id = :id",
                    ))
        return issues
