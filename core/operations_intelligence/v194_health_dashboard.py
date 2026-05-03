from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class HealthDashboard:
    """V194: health dashboard aggregator."""
    def build(self, checks: dict[str, str]) -> IntelligenceArtifact:
        values = list(checks.values())
        bad = sum(1 for x in values if x in {"fail", "blocked", "critical"})
        warn = sum(1 for x in values if x in {"warn", "degraded"})
        score = round((len(values) - bad - 0.5 * warn) / max(1, len(values)), 4)
        status = IntelligenceStatus.BLOCKED if bad else (IntelligenceStatus.WARN if warn else IntelligenceStatus.READY)
        summary = f"health={status.value}, score={score}, checks={len(values)}, warn={warn}, bad={bad}"
        return IntelligenceArtifact(new_id("dashboard"), "health_dashboard", "dashboard", status, score, {"checks": checks, "summary": summary})
