from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class AlterTableDropColumnRule(BaseRule):
    code = "ALTER_TABLE_DROP_COLUMNA"
    name = "ALTER TABLE: eliminación de columna"
    description = "Detecta eliminación de columnas que puede romper aplicaciones y perder datos."
    severity = Severity.CRITICA
    score = 90

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            for alter in stmt.find_all(exp.AlterTable):
                for action in alter.find_all(exp.Drop):
                    col = action.find(exp.Column)
                    if col or "column" in raw_script.lower():
                        issues.append(self._issue(
                            message="ALTER TABLE DROP COLUMN detectado: elimina datos de la columna de forma permanente.",
                            recommendation="Verificar que ninguna aplicación o proceso depende de esta columna antes de eliminarla.",
                        ))
                        break
        return issues
