from typing import List, Set
import sqlglot
from sqlglot import exp
from app.rules.base_rule import BaseRule
from app.models.response_models import Issue, Severity


CRITICAL_TABLES: Set[str] = {
    "DWH_SUKA.ACCOUNT_NUEVA",
    "DWH_SUKA.CAT_SLF_CASES",
    "DWH_SUKA.DIM_RH_SLF",
    "DWH_SUKA.FAC_RPD_REPOSITORIO",
    "DWH_SUKA.FAC_SF_CASES",
    "DWH_SUKA.FAC_SF_TASK",
    "DWH_SUKA.FAC_USER_SLF_N",
    "DWH_SUKA.FAC_VTA_PPTO_DIARIO_D",
    "DWH_SUKA.KOTG903",
    "DWH_SUKA.KOTG981",
    "DWH_SUKA.S999",
    "DWH_SUKA.SAP",
    "DWH_SUKA.SAP_VBAK",
    "DWH_SUKA.SAP_VBAP",
    "DWH_SUKA.SAP_ZSBXTA_TIENDAS",
    "DWH_SUKA.STG_PPTO_VENTA_CENTRAL",
    "DWH_SUKA.STG_RH_POSISIONES_ACTIVAS",
    "DWH_SUKA.STG_VENTA_BO",
    "DWH_SUKA.V_DIM_CANAL_DISTRIBUCION_M",
    "DWH_SUKA.V_DIM_PRODUCTO_M",
    "DWH_SUKA.V_DIM_SUCURSAL_CLIENTE_M",
    "DWH_SUKA.VBPA_SAP",
    "DIM_HK_USUARIOS",
    "DIM_HK_USUARIOS_WINDOWS",
    "DIM_EMPLEADO",
    "VW_RH_POSICIONES_ACTIVAS",
    "DIM_HK_ACESSOS_COMO",
    "DIM_COMO",
    "DIM_HK_INDICADORES",
    "DIM_HK_INDICADOR_CFG",
    "DIM_HK_QUE",
    "DIM_UNIDADES",
    "DIM_HK_FUENTES",
    "DIM_HK_FORMATOS",
    "DIM_HK_TIPOCALCULO",
    "DIM_HK_TIPOAFECTACION",
    "DIM_HK_TOTALACUMUALDO",
    "DIM_HK_CONCEPTOS",
    "FAC_HOSHIN_KANRI_PPTO",
    "FAC_HOSHIN_KANRI_REAL",
    "FAC_HOSHIN_KANRI",
    "FAC_HK_INTEGRAL",
    "FAC_HOSHIN_KANRI_REPOSITORIO_REAL",
    "FAC_HK_CARGAINICIAL",
    "FAC_HK_SEMANAL",
    "FAC_HK_INFSEMANAL",
    "WF_DTS_INVENTARIO",
    "WF_NSC_SBX_NEW",
    "WF_KARDEX_VENTAS",
    "WF_KARDEX_BONIFICACIONES",
    "WF_PRODR_SAP",
    "WF_EXTRACCIONES_SLF_SRV",
    "_0600_D_WF_FAC_SIAP_PARTIDATRATADA",
    "WF_RPD_REPOSITORIO_DET_PPTO",
    "WF_GASTO_KSB1",
    "WF_PA0000",
    "VENTAS_Y_BONIFICACIONES",
    "WF_PA0001",
    "WF_CARGA_DIARIA_SALESFORCE",
    "WF_PA0002",
    "WF_PA0003",
    "WF_PA0006",
    "WF_PA0008",
    "WF_STG_FAC_FLETES",
    "WF_SALESFORCE_ACCOUNT",
    "WF_SALESFORCE_ACCOUNTSHISTORY",
    "WF_SALESFORCE_CANALESDISTRIBUCION",
    "WF_SALESFORCE_CASES",
    "WF_SALESFORCE_CASESHISTORY",
    "WF_SALESFORCE_ESTRUCTURAVENTA",
    "WF_SALESFORCE_LEADS",
    "WF_SALESFORCE_LEADSHISTORY",
    "WF_SALESFORCE_OPPORTUNITIES",
    "WF_SALESFORCE_OPPORTUNITIES_ITEM",
    "WF_SALESFORCE_OPPORTUNITY_ITEMS",
    "WF_SALESFORCE_PEDIDOS",
    "WF_SALESFORCE_PEDIDO_ITEMS",
    "WF_SALESFORCE_PRODUCT",
    "WF_SALESFORCE_RECORDTYPE",
    "WF_SALESFORCE_USERS",
    "WF_SALESFORCE_VISITAS",
    "WF_DTS_INVENTARIO_TTOINTERP_12AM",
    "WF_RPD_REPOSITORIO_DET",
    "WF_ZTHRXXC_00005",
    "WF_CARTERA_SAP",
    "CONTROL_PISO_COPRESI_UNIFICADO",
    "_0530_WF_MOVTO_COSTO_CONSUMO_SIAP",
    "WF_GAINS_PLANEACION",
    "WF_SAP_STG_DWH_MANTTO_ORDENES_TRAJO_NV3",
    "M_CAT_CEROPAPEL_CUADRANTES",
    "WF_ZTHROMXXC_00006",
    "WF_PRD_AGENDA_SANIDAD",
    "WF_TUB_COMPRAS",
    "WF_ENTREGAS_TRANSPORTE_1200",
    "WF_INTEGRACION_MAXMIN",
    "WF_RPD_REPOSITORIO_V2",
    "WF_RESTAURANTES",
    "WF_TUB_ALIMENTACION_NUEVA",
    "WF_TRMFTP_0000",
    "WF_EXTRAE_FECHA_INV_CEDIS_AG_PERIODICO",
    "WF_ZTHROMXXC_00005",
    "WF_GENERA_REPORTE_VTAS",
    "WF_CAT_CLIENTES_LUNES",
    "WF_8089_SEGUIMIENTO_DIARIO_MAYOREO_MM",
    "WF_DTS_INVENTARIO_TTOINTERP",
    "WF_RPD_REPOSITORIO",
    "WF_PEDIDOS_MAX_MIN",
    "WF_RUN_PORTAFOLIO_SKU",
    "WF_FLETES_PT_COMPLETO_SIN_CATALOGOS",
    "WF_ENTREGAS_CON_TRANSPORTE_4H",
    "WF_EXTRACCION_PP1",
    "WF_ENTREGAS_SIN_TRANSPORTE",
    "WF_GASTO_MTTO_PROCESOS",
    "WF_PRD_AGENDA_SC_PRECUARIO",
    "WF_TUBERIA_QUE_JAS",
    "WF_TUB_PAGOS",
    "WF_GASTOS_NUEVO",
    "WF_GASTOS",
    "WF_9023_GASTO_MTTO_PA",
    "WF_LLEVA_FLETES_SAP_TO_ORACLE",
    "WF_GASTOS_GCE",
    "WF_CATALOGOS_MAESTROS",
    "WF_MI_PERFIL",
    "WF_CARGA_DIARIA_TARDE_DET",
    "WF_HRP1000",
    "WF_HRP1001",
    "WF_HRP1002",
    "WF_HRP1007",
    "WF_HRP1008",
    "WF_HRP1013",
    "WF_HRP1014",
    "WF_HRP9101",
    "WF_HRP9103",
    "WF_SLF_CATALOGOCLIENTES",
    "WF_EXTRAE_FECHA_INV_CEDIS_AG",
    "WF_PPTO_2023",
}

_WRITE_STATEMENT_TYPES = (
    exp.Delete,
    exp.Update,
    exp.Insert,
    exp.TruncateTable,
    exp.Drop,
    exp.Merge,
)


class CriticalTableRule(BaseRule):
    code = "TABLA_CRITICA"
    name = "Operación sobre tabla crítica"
    description = "Detecta operaciones de escritura (DML/DDL) sobre tablas catalogadas como críticas para la organización."
    severity = Severity.CRITICA
    score = 80

    def analyze(self, statements: List[sqlglot.Expression], raw_script: str) -> List[Issue]:
        issues = []
        for stmt in statements:
            if not isinstance(stmt, _WRITE_STATEMENT_TYPES):
                continue
            seen = set()
            for table in stmt.find_all(exp.Table):
                key = self._table_key(table)
                if key in CRITICAL_TABLES and key not in seen:
                    seen.add(key)
                    issues.append(self._issue(
                        message=f"Operación de escritura sobre tabla crítica: {key}",
                        recommendation=(
                            f"La tabla '{key}' está catalogada como crítica. "
                            "Verifique que el script cuenta con aprobación explícita antes de ejecutarse en producción."
                        ),
                    ))
        return issues

    @staticmethod
    def _table_key(table: exp.Table) -> str:
        name = table.name.upper()
        db = table.db.upper() if table.db else ""
        return f"{db}.{name}" if db else name
