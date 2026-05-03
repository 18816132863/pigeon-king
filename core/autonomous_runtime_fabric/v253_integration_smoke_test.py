from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, FabricGate, new_id

class IntegrationSmokeTest:
    """V253: integration smoke test suite."""
    def run(self, checks: dict[str, bool]) -> FabricArtifact:
        failed = [k for k, v in checks.items() if not v]
        gate = FabricGate.FAIL if failed else FabricGate.PASS
        status = FabricStatus.BLOCKED if failed else FabricStatus.READY
        score = 1 - len(failed) / max(1, len(checks))
        return FabricArtifact(new_id("smoke"), "integration_smoke_test", "test", status, score, {"failed": failed, "gate": gate.value})
