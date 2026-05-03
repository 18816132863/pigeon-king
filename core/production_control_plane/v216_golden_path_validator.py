from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, new_id

class GoldenPathValidator:
    """V216: golden path validator."""
    def validate(self, paths: list[str]) -> ControlArtifact:
        required = ["package", "apply_script", "verify_script", "pass_marker"]
        present = {r: any(r in p for p in paths) for r in required}
        score = sum(1 for v in present.values() if v) / len(required)
        status = PlaneStatus.READY if score == 1 else PlaneStatus.WARN
        return ControlArtifact(new_id("golden"), "golden_path", "validation", status, score, {"present": present})
