from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class DataQualityGate:
    """V172: data quality gate."""
    def evaluate(self, ingestion_artifact) -> IntelligenceArtifact:
        sources = ingestion_artifact.payload.get("sources", [])
        total_records = sum(x.get("records", 0) for x in sources)
        untrusted = [x["id"] for x in sources if not x.get("trusted")]
        completeness = 1.0 if total_records > 0 else 0.0
        trust_score = 1 - len(untrusted) / max(1, len(sources))
        score = round(completeness * 0.5 + trust_score * 0.5, 4)
        status = IntelligenceStatus.READY if score >= 0.75 else IntelligenceStatus.WARN
        return IntelligenceArtifact(new_id("dq"), "data_quality_gate", "data_quality", status, score, {"total_records": total_records, "untrusted": untrusted})
