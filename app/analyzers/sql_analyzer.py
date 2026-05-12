import re
from typing import List
import sqlglot
from sqlglot import exp
from app.core.exceptions import SQLParseException
from app.core.logging_config import get_logger
from app.models.response_models import Statistics

logger = get_logger(__name__)

_STMT_SPLIT = re.compile(r';\s*(?=\n|$)', re.MULTILINE)


class SQLAnalyzer:

    def parse(self, script: str, dialect: str) -> List[sqlglot.Expression]:
        script = script.replace('\r\n', '\n').replace('\r', '\n')

        valid = self._parse_full(script, dialect)
        if not valid:
            valid = self._parse_by_statement(script, dialect)

        if not valid:
            raise SQLParseException("No se encontraron sentencias SQL válidas en el script.")

        logger.info(f"Parsed {len(valid)} statement(s) with dialect '{dialect}'")
        return valid

    def _parse_full(self, script: str, dialect: str) -> List[sqlglot.Expression]:
        try:
            result = sqlglot.parse(script, dialect=dialect, error_level=sqlglot.ErrorLevel.WARN)
            return [s for s in result if s is not None]
        except Exception:
            return []

    def _parse_by_statement(self, script: str, dialect: str) -> List[sqlglot.Expression]:
        valid = []
        chunks = [c.strip() for c in _STMT_SPLIT.split(script) if c.strip()]
        for chunk in chunks:
            try:
                result = sqlglot.parse(chunk, dialect=dialect, error_level=sqlglot.ErrorLevel.IGNORE)
                valid.extend([s for s in result if s is not None])
            except Exception:
                pass
        return valid

    def extract_statistics(self, statements: List[sqlglot.Expression]) -> Statistics:
        tables: set[str] = set()
        deletes = updates = selects = inserts = drops = truncates = 0

        for stmt in statements:
            if isinstance(stmt, exp.Delete):
                deletes += 1
            elif isinstance(stmt, exp.Update):
                updates += 1
            elif isinstance(stmt, exp.Select):
                selects += 1
            elif isinstance(stmt, exp.Insert):
                inserts += 1
            elif isinstance(stmt, exp.Drop):
                drops += 1
            elif isinstance(stmt, exp.TruncateTable):
                truncates += 1

            for table in stmt.find_all(exp.Table):
                if table.name:
                    tables.add(table.name.lower())

        return Statistics(
            tablasAfectadas=len(tables),
            sentenciasDelete=deletes,
            sentenciasUpdate=updates,
            sentenciasSelect=selects,
            sentenciasInsert=inserts,
            sentenciasDrop=drops,
            sentenciasTruncate=truncates,
            totalSentencias=len(statements),
        )
