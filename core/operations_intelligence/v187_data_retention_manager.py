from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class DataRetentionManager:
    """V187: data retention and deletion policy manager."""
    def policy(self, data_kind: str) -> IntelligenceArtifact:
        if data_kind in {"secret", "credential"}:
            retention = "do_not_store_raw"
            deletion = "immediate_redaction"
        elif data_kind in {"audit", "evidence"}:
            retention = "keep_until_project_close"
            deletion = "manual_review_before_delete"
        else:
            retention = "compact_after_90_days"
            deletion = "safe_archive_or_delete"
        return IntelligenceArtifact(new_id("retention"), "data_retention_policy", "retention", IntelligenceStatus.READY, 0.88, {"data_kind": data_kind, "retention": retention, "deletion": deletion})
