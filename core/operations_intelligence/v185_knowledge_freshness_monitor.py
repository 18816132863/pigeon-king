from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class KnowledgeFreshnessMonitor:
    """V185: knowledge freshness monitor."""
    def assess(self, topic: str, days_old: int) -> IntelligenceArtifact:
        if days_old <= 7:
            status = "fresh"
            score = 0.95
        elif days_old <= 60:
            status = "acceptable"
            score = 0.78
        else:
            status = "stale_requires_lookup"
            score = 0.45
        artifact_status = IntelligenceStatus.READY if score >= 0.75 else IntelligenceStatus.WARN
        return IntelligenceArtifact(new_id("fresh"), "knowledge_freshness", "freshness", artifact_status, score, {"topic": topic, "days_old": days_old, "freshness": status})
