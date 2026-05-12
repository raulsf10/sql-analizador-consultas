from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class MassiveMergeRule(BaseRule):
    code = "MERGE_MASIVO"
    name = "MERGE masivo"
    description = "Detecta uso de MERGE que puede escalar bloques y deadlocks en tablas grandes."
    severity = Severity.ALTA
    score = 60

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            if stmt.find(exp.Merge):
                issues.append(self._issue(
                    message="MERGE detectado: puede causar bloqueos escalados y deadlocks en tablas de gran volumen.",
                    recommendation="En inserciones/actualizaciones masivas, considerar INSERT+UPDATE por separado o usar MERGE con HOLDLOCK.",
                ))
        return issues
