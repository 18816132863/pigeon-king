from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, new_id

class DataLineageTracker:
    """V202: data lineage tracker."""
    def trace(self, sources: list[str], outputs: list[str]) -> ControlArtifact:
        lineage = [{"source": s, "outputs": outputs, "transform": "controlled_agent_processing"} for s in sources]
        score = 0.9 if sources and outputs else 0.6
        status = PlaneStatus.READY if score >= 0.75 else PlaneStatus.WARN
        return ControlArtifact(new_id("lineage"), "data_lineage", "lineage", status, score, {"lineage": lineage})
