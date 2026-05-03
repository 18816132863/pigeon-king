from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, new_id

class ConnectorQuotaManager:
    """V209: connector quota manager."""
    def evaluate(self, usage: dict[str, int], limits: dict[str, int]) -> ControlArtifact:
        over = [k for k, v in usage.items() if v > limits.get(k, 10**9)]
        near = [k for k, v in usage.items() if v >= limits.get(k, 10**9) * 0.8 and k not in over]
        status = PlaneStatus.BLOCKED if over else (PlaneStatus.WARN if near else PlaneStatus.READY)
        score = 1 - (len(over) * 0.5 + len(near) * 0.2) / max(1, len(limits))
        return ControlArtifact(new_id("quota"), "connector_quota", "quota", status, max(0, round(score, 4)), {"over": over, "near": near})
