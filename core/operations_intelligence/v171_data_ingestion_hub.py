from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class DataIngestionHub:
    """V171: normalized data ingestion hub."""
    def ingest(self, sources: list[dict]) -> IntelligenceArtifact:
        normalized = []
        for idx, src in enumerate(sources):
            normalized.append({
                "id": src.get("id", f"source_{idx}"),
                "kind": src.get("kind", "unknown"),
                "records": int(src.get("records", 1)),
                "trusted": bool(src.get("trusted", True)),
            })
        trusted_ratio = sum(1 for x in normalized if x["trusted"]) / max(1, len(normalized))
        return IntelligenceArtifact(new_id("ingest"), "data_ingestion", "data", IntelligenceStatus.READY, round(trusted_ratio, 4), {"sources": normalized})
