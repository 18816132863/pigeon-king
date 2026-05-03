from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, new_id

class ObjectiveAlignmentEngine:
    """V224: objective alignment checker."""
    def align(self, objectives: list[str], deliverables: list[str]) -> ControlArtifact:
        matched = []
        for obj in objectives:
            matched.append(any(token in " ".join(deliverables) for token in obj.split()))
        score = sum(1 for x in matched if x) / max(1, len(objectives))
        status = PlaneStatus.READY if score >= 0.75 else PlaneStatus.WARN
        return ControlArtifact(new_id("align"), "objective_alignment", "alignment", status, score, {"objectives": objectives, "matched": matched})
