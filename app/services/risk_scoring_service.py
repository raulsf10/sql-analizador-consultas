from typing import List
from app.models.response_models import Issue, Criticality


class RiskScoringService:

    _THRESHOLDS = [
        (81, Criticality.CRITICA),
        (61, Criticality.ALTA),
        (31, Criticality.MEDIA),
        (0,  Criticality.BAJA),
    ]

    def calculate_score(self, issues: List[Issue]) -> int:
        total = sum(i.puntuacion for i in issues)
        return min(total, 100)

    def get_criticality(self, score: int) -> Criticality:
        for threshold, level in self._THRESHOLDS:
            if score >= threshold:
                return level
        return Criticality.BAJA

    def requires_approval(self, score: int, threshold: int = 60) -> bool:
        return score > threshold
