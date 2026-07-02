import re
from typing import List
import sqlglot
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity

# Active Oracle optimizer hint: /*+ ... PARALLEL ... */
# The '+' after '/*' is mandatory — without it is a regular comment Oracle ignores.
_HINT_RE = re.compile(
    r'/\*\+(?:[^*]|\*(?!/))*\bPARALLEL\b(?:[^*]|\*(?!/))*\*/',
    re.IGNORECASE | re.DOTALL,
)

# PARALLEL used directly as a SQL keyword outside of hints,
# e.g.: ALTER TABLE t PARALLEL 4  /  ALTER SESSION FORCE PARALLEL QUERY
# Matches are filtered in analyze() to exclude positions already inside hint blocks.
_KEYWORD_RE = re.compile(r'\bPARALLEL\b', re.IGNORECASE)


class ParallelHintRule(BaseRule):
    code = "PARALLEL_HINT"
    name = "Uso de PARALLEL"
    description = (
        "Detecta el uso de PARALLEL como hint activo de Oracle (/*+ PARALLEL */) "
        "o como keyword directo en SQL. El paralelismo forzado puede saturar CPU e I/O "
        "del servidor en producción y causar contención severa."
    )
    severity = Severity.CRITICA
    score = 80

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)
        issues = []
        seen_lines: set[int] = set()

        # 1. Active Oracle hints: /*+ PARALLEL(...) */
        for match in _HINT_RE.finditer(raw_script):
            line = raw_script[: match.start()].count("\n") + 1
            if line in seen_lines:
                continue
            seen_lines.add(line)
            hint_text = match.group(0).strip()
            issues.append(
                self._issue(
                    message=(
                        f"Hint PARALLEL activo detectado: '{hint_text}'. "
                        "Fuerza ejecución paralela y puede saturar recursos del servidor."
                    ),
                    recommendation=(
                        "Eliminar el hint PARALLEL del script. "
                        "El paralelismo debe ser controlado por el DBA a nivel de sesión "
                        "o de objeto, nunca embebido en las consultas."
                    ),
                    line=line,
                )
            )

        # 2. PARALLEL as a direct SQL keyword (DDL / ALTER SESSION)
        hint_ranges = {(m.start(), m.end()) for m in _HINT_RE.finditer(raw_script)}
        for match in _KEYWORD_RE.finditer(raw_script):
            if any(start <= match.start() < end for start, end in hint_ranges):
                continue
            line = raw_script[: match.start()].count("\n") + 1
            if line in seen_lines:
                continue
            seen_lines.add(line)
            issues.append(
                self._issue(
                    message=(
                        "Keyword PARALLEL detectado directamente en el script. "
                        "Fuerza ejecución paralela y puede saturar recursos del servidor."
                    ),
                    recommendation=(
                        "Eliminar el uso de PARALLEL del script. "
                        "El paralelismo debe ser controlado por el DBA a nivel de sesión "
                        "o de objeto, nunca embebido en las consultas."
                    ),
                    line=line,
                )
            )
        return issues
