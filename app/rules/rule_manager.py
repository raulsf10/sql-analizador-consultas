from typing import Dict, List
from app.rules.base_rule import BaseRule
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RuleManager:
    def __init__(self) -> None:
        self._rules: Dict[str, BaseRule] = {}

    def register(self, rule: BaseRule) -> None:
        self._rules[rule.code] = rule
        logger.debug(f"Rule registered: {rule.code}")

    def get_all(self) -> List[BaseRule]:
        return list(self._rules.values())
