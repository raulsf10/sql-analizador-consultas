import re as _re
from abc import ABC, abstractmethod
from typing import List, Optional
import sqlglot
from app.models.response_models import Issue, Severity


class BaseRule(ABC):
    code: str = ""
    name: str = ""
    description: str = ""
    severity: Severity = Severity.BAJA
    score: int = 0
    _current_raw_script: str = ""

    @abstractmethod
    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        """Analyze parsed AST statements and return a list of issues found."""

    def _set_script(self, raw_script: str) -> None:
        self._current_raw_script = raw_script

    def _issue(
        self,
        message: str,
        recommendation: str,
        line: Optional[int] = None,
        node: Optional[sqlglot.Expression] = None,
    ) -> Issue:
        if line is None and node is not None:
            line = self._line(node)
        return Issue(
            codigo=self.code,
            severidad=self.severity,
            mensaje=message,
            linea=line,
            recomendacion=recommendation,
            puntuacion=self.score,
        )

    def _line(self, node: Optional[sqlglot.Expression]) -> Optional[int]:
        if node is None:
            return None
        val = node.meta.get("line")
        if val is not None:
            return int(val)
        if self._current_raw_script:
            return self._search_line(node, self._current_raw_script)
        return None

    @staticmethod
    def _search_line(node: sqlglot.Expression, raw_script: str) -> Optional[int]:
        try:
            node_sql = node.sql(dialect="oracle").strip()
        except Exception:
            return None
        if not node_sql:
            return None

        lines = raw_script.splitlines()
        lower_lines = [ll.lower() for ll in lines]
        sql_lower = node_sql.lower()

        # Try progressively shorter prefixes (handles multi-line nodes)
        for length in (len(sql_lower), 50, 30, 15, 8):
            if length > len(sql_lower):
                continue
            chunk = sql_lower[:length].strip()
            if len(chunk) < 4:
                break
            for i, ll in enumerate(lower_lines, 1):
                if chunk in ll:
                    return i

        # Fallback: word-pair search
        words = sql_lower.split()
        for j in range(len(words) - 1):
            pair = (words[j] + " " + words[j + 1]).strip("(),;")
            if len(pair) >= 4:
                for i, ll in enumerate(lower_lines, 1):
                    if pair in ll:
                        return i

        # Fallback: first word >= 4 chars (whole-word match)
        for word in words:
            word = word.strip("(),;").lower()
            if len(word) >= 4:
                for i, ll in enumerate(lower_lines, 1):
                    if _re.search(r"\b" + _re.escape(word) + r"\b", ll, _re.IGNORECASE):
                        return i
                break

        return None

    @staticmethod
    def _keyword_line(raw_script: str, keyword: str) -> Optional[int]:
        kw = keyword.lower()
        for i, text in enumerate(raw_script.splitlines(), start=1):
            if kw in text.lower():
                return i
        return None
