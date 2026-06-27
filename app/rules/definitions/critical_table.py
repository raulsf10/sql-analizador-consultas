from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity
from app.db import catalog_repository

_WRITE_STATEMENT_TYPES = tuple(filter(None, [
    getattr(exp, "AlterTable", None),
    exp.Delete,
    exp.Drop,
    exp.Insert,
    exp.Merge,
    exp.TruncateTable,
    exp.Update,
]))


def _write_target_tables(stmt: sqlglot.Expression) -> list[exp.Table]:
    """Return only the tables being written/modified — ignores source/join tables."""
    if isinstance(stmt, exp.TruncateTable):
        # TRUNCATE has no subqueries; all referenced tables are targets
        return list(stmt.find_all(exp.Table))
    target = getattr(stmt, "this", None)
    if target is None:
        return []
    if isinstance(target, exp.Table):
        return [target]
    # INSERT INTO schema.table(cols) → stmt.this is exp.Schema wrapping exp.Table
    found = target.find(exp.Table)
    return [found] if found else []


class CriticalTableRule(BaseRule):
    code = "TABLA_CRITICA"
    name = "Operación de escritura sobre tabla crítica"
    description = "Detecta operaciones de escritura (INSERT, UPDATE, DELETE, TRUNCATE, DROP, ALTER, MERGE) sobre tablas catalogadas como críticas. Las lecturas (SELECT) no se penalizan."
    severity = Severity.CRITICA
    score = 100

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)
        issues = []
        for stmt in statements:
            if not isinstance(stmt, _WRITE_STATEMENT_TYPES):
                continue
            seen = set()
            for table in _write_target_tables(stmt):
                display = self._display_key(table)
                if self._is_critical(table) and display not in seen:
                    seen.add(display)
                    issues.append(self._issue(
                        message=f"Operación de escritura sobre tabla crítica: {display}",
                        recommendation=(
                            f"La tabla '{display}' está catalogada como crítica. "
                            "Verifique que el script cuenta con aprobación explícita antes de ejecutarse en producción."
                        ),
                        node=stmt,
                    ))
        return issues

    @staticmethod
    def _display_key(table: exp.Table) -> str:
        name = table.name.upper()
        db = table.db.upper() if table.db else ""
        return f"{db}.{name}" if db else name

    @staticmethod
    def _is_critical(table: exp.Table) -> bool:
        name = table.name.upper()
        db = table.db.upper() if table.db else ""
        full_key = f"{db}.{name}" if db else name
        # Matches both "DWH_SUKA.DIM_HK_INDICADORES" and "DIM_HK_INDICADORES"
        tables = catalog_repository.get_critical_tables()
        return full_key in tables or name in tables
