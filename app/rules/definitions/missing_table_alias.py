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
        self._set_script(raw_script)

        # For each line, keep the SELECT with the most tables without alias.
        # Deduplicating by line prevents a deeply nested query from generating
        # a separate entry for each SELECT level that happens to map to the same line.
        best: dict[object, tuple[list[str], exp.Expression]] = {}

        for stmt in statements:
            for select in stmt.find_all(exp.Select):
                if not select.find(exp.Join):
                    continue
                if not select.find(exp.From):
                    continue
                tables_no_alias = [t.name for t in select.find_all(exp.Table) if not t.alias]
                if not tables_no_alias:
                    continue
                line = self._line(select)
                if line not in best or len(tables_no_alias) > len(best[line][0]):
                    best[line] = (tables_no_alias, select)

        issues = []
        for line_key in sorted(best, key=lambda k: k or 0):
            tables, node = best[line_key]
            # Deduplicate case-insensitively (DIM_CALENDARIO == dim_calendario in Oracle)
            seen_lower: set[str] = set()
            unique: list[str] = []
            for t in tables:
                if t.lower() not in seen_lower:
                    seen_lower.add(t.lower())
                    unique.append(t)
            display = ", ".join(unique[:5])
            if len(unique) > 5:
                display += f" y {len(unique) - 5} más"
            issues.append(self._issue(
                message=f"Tablas sin alias en consulta con JOIN: {display}.",
                recommendation="Agregar alias cortos a todas las tablas en consultas con JOINs. Ejemplo: FROM clientes c JOIN pedidos p ON c.id = p.cliente_id",
                node=node,
            ))
        return issues
