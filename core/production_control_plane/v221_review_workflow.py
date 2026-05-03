from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, new_id

class ReviewWorkflow:
    """V221: review workflow manager."""
    def create(self, artifact_names: list[str], reviewers: list[str]) -> ControlArtifact:
        items = [{"artifact": a, "reviewer": reviewers[i % len(reviewers)] if reviewers else "owner", "status": "pending"} for i, a in enumerate(artifact_names)]
        return ControlArtifact(new_id("review"), "review_workflow", "review", PlaneStatus.READY, 0.86, {"items": items})
