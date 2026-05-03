from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, GateDecision, new_id

class ContractTestRunner:
    """V215: contract test runner."""
    def run(self, contracts: dict[str, bool]) -> ControlArtifact:
        failed = [k for k, v in contracts.items() if not v]
        decision = GateDecision.FAIL if failed else GateDecision.PASS
        status = PlaneStatus.BLOCKED if failed else PlaneStatus.READY
        score = 1 - len(failed) / max(1, len(contracts))
        return ControlArtifact(new_id("contract_test"), "contract_tests", "test", status, score, {"failed": failed, "decision": decision.value})
