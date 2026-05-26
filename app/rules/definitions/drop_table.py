from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class DropTableRule(BaseRule):
    code = "DROP_TABLA"
    name = "DROP TABLE: eliminar tabla"
    description = "Detecta DROP TABLE que elimina la estructura y datos de una tabla permanentemente."
    severity = Severity.CRITICA
    score = 100

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)
        issues = []
        for stmt in statements:
            for drop in stmt.find_all(exp.Drop):
                kind = (drop.args.get("kind") or "").upper()
                if kind == "TABLE":
                    table_name = ""
                    t = drop.find(exp.Table)
                    if t:
                        table_name = t.name
                    issues.append(self._issue(
                        message=f"DROP TABLE detectado{f' sobre: {table_name}' if table_name else ''}: destruye la tabla y sus datos permanentemente.",
                        recommendation="Esta operación es irreversible. Asegurarse de tener respaldo y aprobación de DBA.",
                        node=drop,
                    ))
        return issues
