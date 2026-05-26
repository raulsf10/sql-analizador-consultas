from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class DynamicExecRule(BaseRule):
    code = "EXEC_DINAMICO"
    name = "EXEC / EXECUTE dinámico"
    description = "Detecta EXEC con concatenación de cadenas que expone a SQL Injection."
    severity = Severity.ALTA
    score = 80

    _EXEC_KEYWORDS = {"exec", "execute", "sp_executesql"}

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)
        issues = []
        lower = raw_script.lower()
        for kw in self._EXEC_KEYWORDS:
            if kw in lower:
                # Look for string concatenation patterns near EXEC
                idx = lower.find(kw)
                context = lower[idx:idx + 200]
                if "+" in context or "||" in context or "concat" in context:
                    issues.append(self._issue(
                        message=f"EXEC dinámico con concatenación detectado: alto riesgo de SQL Injection.",
                        recommendation="Usar sp_executesql con parámetros tipados en lugar de concatenación de strings.",
                        line=self._keyword_line(raw_script, kw),
                    ))
                    break
        # Also check via AST for Anonymous EXEC calls
        for stmt in statements:
            for anon in stmt.find_all(exp.Anonymous):
                if anon.name.lower() in self._EXEC_KEYWORDS:
                    issues.append(self._issue(
                        message="Llamada a EXEC/EXECUTE detectada via AST.",
                        recommendation="Parametrizar las consultas dinámicas usando sp_executesql con @params.",
                        node=anon,
                    ))
                    break
        return issues
