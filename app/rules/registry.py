from app.rules.rule_manager import RuleManager
from app.rules.definitions.delete_without_where import DeleteWithoutWhereRule
from app.rules.definitions.update_without_where import UpdateWithoutWhereRule
from app.rules.definitions.select_star import SelectStarRule
from app.rules.definitions.nolock_usage import NolockUsageRule
from app.rules.definitions.not_in_usage import NotInUsageRule
from app.rules.definitions.truncate_table import TruncateTableRule
from app.rules.definitions.drop_table import DropTableRule
from app.rules.definitions.alter_table_drop_column import AlterTableDropColumnRule
from app.rules.definitions.dynamic_exec import DynamicExecRule
from app.rules.definitions.xp_cmdshell import XpCmdshellRule
from app.rules.definitions.distinct_on_join import DistinctOnJoinRule
from app.rules.definitions.correlated_subquery import CorrelatedSubqueryRule
from app.rules.definitions.function_on_indexed_column import FunctionOnIndexedColumnRule
from app.rules.definitions.date_as_text import DateAsTextRule
from app.rules.definitions.type_mismatch_where import TypeMismatchWhereRule
from app.rules.definitions.calculated_column_filter import CalculatedColumnFilterRule
from app.rules.definitions.cte_reuse import CteReuseRule
from app.rules.definitions.missing_table_alias import MissingTableAliasRule
from app.rules.definitions.excessive_or import ExcessiveOrRule
from app.rules.definitions.select_without_alias_join import SelectWithoutAliasJoinRule
from app.rules.definitions.massive_merge import MassiveMergeRule
from app.rules.definitions.in_subquery import InSubqueryRule
from app.rules.definitions.incorrect_order_by import IncorrectOrderByRule
from app.rules.definitions.pivot_unpivot import PivotUnpivotRule
from app.rules.definitions.subquery_instead_of_join import SubqueryInsteadOfJoinRule
from app.rules.definitions.critical_table import CriticalTableRule
from app.rules.definitions.tautological_where import TautologicalWhereRule
from app.rules.definitions.no_bind_variable import NoBindVariableRule
from app.rules.definitions.duplicate_expression import DuplicateExpressionRule
from app.rules.definitions.parallel_hint import ParallelHintRule


def build_rule_manager() -> RuleManager:
    manager = RuleManager()
    rules = [
        DeleteWithoutWhereRule(),
        UpdateWithoutWhereRule(),
        SelectStarRule(),
        NolockUsageRule(),
        NotInUsageRule(),
        TruncateTableRule(),
        DropTableRule(),
        AlterTableDropColumnRule(),
        DynamicExecRule(),
        XpCmdshellRule(),
        DistinctOnJoinRule(),
        CorrelatedSubqueryRule(),
        FunctionOnIndexedColumnRule(),
        DateAsTextRule(),
        TypeMismatchWhereRule(),
        CalculatedColumnFilterRule(),
        CteReuseRule(),
        MissingTableAliasRule(),
        ExcessiveOrRule(),
        SelectWithoutAliasJoinRule(),
        MassiveMergeRule(),
        InSubqueryRule(),
        IncorrectOrderByRule(),
        PivotUnpivotRule(),
        SubqueryInsteadOfJoinRule(),
        CriticalTableRule(),
        TautologicalWhereRule(),
        NoBindVariableRule(),
        DuplicateExpressionRule(),
        ParallelHintRule(),
    ]
    for rule in rules:
        manager.register(rule)
    return manager
