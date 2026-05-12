from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class CorrelatedSubqueryRule(BaseRule):
    code = "SUBCONSULTA_CORRELACIONADA"
    name = "Subconsulta correlacionada"
    description = "Detecta subconsultas en WHERE que se ejecutan una vez por cada fila de la consulta externa."
    severity = Severity.ALTA
    score = 50

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            for select in stmt.find_all(exp.Select):
                where = select.find(exp.Where)
                if not where:
                    continue

                # Collect alias/names of tables in the outer query's FROM
                outer_table_names: set[str] = set()
                from_clause = select.find(exp.From)
                if from_clause:
                    for tbl in from_clause.find_all(exp.Table):
                        name = (tbl.alias or tbl.name or "").lower()
                        if name:
                            outer_table_names.add(name)
                for join in select.find_all(exp.Join):
                    for tbl in join.find_all(exp.Table):
                        name = (tbl.alias or tbl.name or "").lower()
                        if name:
                            outer_table_names.add(name)

                if not outer_table_names:
                    continue

                for subq in where.find_all(exp.Subquery):
                    for col in subq.find_all(exp.Column):
                        table_ref = (col.table or "").lower()
                        if table_ref and table_ref in outer_table_names:
                            issues.append(self._issue(
                                message="Subconsulta correlacionada detectada en WHERE: se ejecuta N veces (una por fila).",
                                recommendation="Reemplazar con JOIN o CTE para mejorar rendimiento.",
                            ))
                            break
        return issues
