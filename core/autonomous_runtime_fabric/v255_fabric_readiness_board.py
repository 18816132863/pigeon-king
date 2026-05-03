from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, FabricGate, new_id

class FabricReadinessBoard:
    """V255: fabric readiness decision board."""
    def decide(self, artifacts: list) -> FabricArtifact:
        blocked = [a.name for a in artifacts if a.status.value == "blocked"]
        warn = [a.name for a in artifacts if a.status.value in {"warn", "degraded"}]
        avg = sum(a.score for a in artifacts) / max(1, len(artifacts))
        if blocked:
            gate, status = FabricGate.FAIL, FabricStatus.BLOCKED
        elif avg < 0.75:
            gate, status = FabricGate.WARN, FabricStatus.WARN
        elif warn:
            gate, status = FabricGate.WARN, FabricStatus.WARN
        else:
            gate, status = FabricGate.PASS, FabricStatus.READY
        return FabricArtifact(new_id("readiness"), "fabric_readiness_board", "readiness", status, round(avg, 4), {"gate": gate.value, "blocked": blocked, "warn": warn})
