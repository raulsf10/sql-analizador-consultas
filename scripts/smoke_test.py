"""Quick smoke test — run with: .venv\Scripts\python.exe scripts\smoke_test.py"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rules.registry import build_rule_manager
from app.analyzers.sql_analyzer import SQLAnalyzer
from app.services.risk_scoring_service import RiskScoringService
from app.services.analysis_service import AnalysisService
from app.models.request_models import AnalyzeRequest

rm = build_rule_manager()
svc = AnalysisService(rm, SQLAnalyzer(), RiskScoringService())

cases = [
    ("oracle", "DELETE FROM usuarios;"),
    ("tsql",   "UPDATE clientes SET activo = 0;"),
    ("tsql",   "DROP TABLE dbo.pedidos;"),
    ("tsql",   "TRUNCATE TABLE logs_sistema;"),
    ("postgres","SELECT * FROM ventas;"),
    ("tsql",   "SELECT * FROM ventas v WITH (NOLOCK) JOIN clientes c ON v.id = c.id WHERE UPPER(c.nombre) = 'JUAN';"),
    ("tsql",   "SELECT id, nombre FROM productos WHERE fecha_creacion = '2024-01-15';"),
    ("oracle", "SELECT id FROM pedidos WHERE id NOT IN (SELECT pedido_id FROM detalle_pedidos);"),
]

print(f"\n{'Score':>5}  {'Criticality':<10}  {'Issues':>6}  SQL")
print("-" * 90)
for dialect, sql in cases:
    r = svc.analyze(AnalyzeRequest(dialect=dialect, script=sql))
    print(f"  {r.score:>3}  [{r.criticality.value:<8}]  {len(r.issues):>6}  {sql[:70]}")
    for issue in r.issues:
        print(f"        -> [{issue.severity.value}] {issue.ruleCode} (+{issue.scoreContribution})")

print(f"\nTotal rules loaded: {len(rm.get_all())}")
print("Smoke test OK")
