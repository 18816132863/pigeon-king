from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class MetricsKPIEngine:
    """V170: KPI and metric engine."""
    def compute(self, artifacts: list) -> IntelligenceArtifact:
        total = len(artifacts)
        ready = sum(1 for a in artifacts if getattr(a, "status", None).value == "ready")
        avg_score = round(sum(getattr(a, "score", 0) for a in artifacts) / max(1, total), 4)
        kpis = {
            "artifact_total": total,
            "ready_ratio": round(ready / max(1, total), 4),
            "avg_score": avg_score,
            "release_readiness": round((ready / max(1, total)) * 0.6 + avg_score * 0.4, 4),
        }
        return IntelligenceArtifact(new_id("kpi"), "metrics_kpi", "metrics", IntelligenceStatus.READY, kpis["release_readiness"], kpis)
