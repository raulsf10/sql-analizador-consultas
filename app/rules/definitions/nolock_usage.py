from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class NolockUsageRule(BaseRule):
    code = "USO_NOLOCK"
    name = "Uso de NOLOCK / READUNCOMMITTED"
    description = "Detecta el hint NOLOCK o READUNCOMMITTED que causa lecturas sucias."
    severity = Severity.MEDIA
    score = 30

    _HINTS = {"nolock", "readuncommitted"}

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        self._set_script(raw_script)
        issues = []
        for stmt in statements:
            for hint in stmt.find_all(exp.WithTableHint):
                for h in hint.find_all(exp.Var):
                    if h.name.lower() in self._HINTS:
                        issues.append(self._issue(
                            message=f"Uso de hint {h.name.upper()}: puede causar lecturas sucias (dirty reads).",
                            recommendation="Evitar NOLOCK. Usar niveles de aislamiento adecuados (READ COMMITTED SNAPSHOT) o revisar la necesidad real.",
                            node=h,
                        ))
                        break
        # Also catch raw text mentions for dialects that may not fully parse hints
        lower_script = raw_script.lower()
        if ("nolock" in lower_script or "readuncommitted" in lower_script) and not issues:
            hint_kw = "nolock" if "nolock" in lower_script else "readuncommitted"
            issues.append(self._issue(
                message="Posible uso de NOLOCK / READUNCOMMITTED detectado en script.",
                recommendation="Evitar NOLOCK. Revisar nivel de aislamiento de transacciones.",
                line=self._keyword_line(raw_script, hint_kw),
            ))
        return issues
