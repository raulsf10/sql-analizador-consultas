from typing import List
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


class XpCmdshellRule(BaseRule):
    code = "XP_CMDSHELL"
    name = "Uso de xp_cmdshell"
    description = "Detecta xp_cmdshell que permite ejecutar comandos del sistema operativo desde SQL Server."
    severity = Severity.CRITICA
    score = 100

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        if "xp_cmdshell" in raw_script.lower():
            issues.append(self._issue(
                message="xp_cmdshell detectado: permite ejecutar comandos del SO desde SQL Server. Riesgo de seguridad extremo.",
                recommendation="Deshabilitar xp_cmdshell con: EXEC sp_configure 'xp_cmdshell', 0. Usar alternativas seguras.",
            ))
        return issues
