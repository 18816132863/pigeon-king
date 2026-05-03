from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, new_id

class TrainingDataCurator:
    """V220: training/eval data curator."""
    def curate(self, examples: list[dict]) -> ControlArtifact:
        safe = []
        rejected = []
        for e in examples:
            text = str(e.get("text", ""))
            if any(x in text.lower() for x in ["api_key", "token", "secret", "密码", "密钥"]):
                rejected.append(e.get("id", "unknown"))
            else:
                safe.append(e)
        score = len(safe) / max(1, len(examples))
        status = PlaneStatus.READY if not rejected else PlaneStatus.WARN
        return ControlArtifact(new_id("curate"), "training_data_curation", "data", status, score, {"safe_count": len(safe), "rejected": rejected})
