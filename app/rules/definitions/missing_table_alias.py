from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class MissingTableAliasRule(BaseRule):
    code = "ALIAS_TABLA_FALTANTE"
    name = "Falta de alias en tablas con JOIN"
    description = "Detecta consultas con JOINs donde las tablas no tienen alias, reduciendo legibilidad."
    severity = Severity.BAJA
    score = 10

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            for select in stmt.find_all(exp.Select):
                if not select.find(exp.Join):
                    continue
                from_clause = select.find(exp.From)
                if not from_clause:
                    continue
                tables_without_alias = []
                for table in select.find_all(exp.Table):
                    if not table.alias:
                        tables_without_alias.append(table.name)
                if tables_without_alias:
                    issues.append(self._issue(
                        message=f"Tablas sin alias en consulta con JOIN: {', '.join(tables_without_alias[:3])}.",
                        recommendation="Agregar alias cortos a todas las tablas en consultas con JOINs. Ejemplo: FROM clientes c JOIN pedidos p ON c.id = p.cliente_id",
                    ))
        return issues
