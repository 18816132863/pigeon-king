from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .schemas import ReleaseGateResult, ReleaseStage, new_id, dataclass_to_dict
from .storage import JsonStore


class ReleaseGovernor:
    """V106: release gates for autonomy/operating-agent upgrades."""

    def __init__(self, root: str | Path = ".operating_agent_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "release_gate_results.json")

    def evaluate_release(
        self,
        constitution_ok: bool,
        permissions_ok: bool,
        sandbox_ok: bool,
        benchmark_score: float,
        recovery_ok: bool,
        mcp_ok: bool,
    ) -> ReleaseGateResult:
        gates = {
            "constitution_ok": constitution_ok,
            "permissions_ok": permissions_ok,
            "sandbox_ok": sandbox_ok,
            "benchmark_ok": benchmark_score >= 0.8,
            "recovery_ok": recovery_ok,
            "mcp_ok": mcp_ok,
        }
        blockers = [k for k, v in gates.items() if not v]
        score = round(sum(1 for v in gates.values() if v) / len(gates), 4)
        if blockers:
            stage = ReleaseStage.BLOCKED
        elif score >= 0.95:
            stage = ReleaseStage.STABLE
        elif score >= 0.8:
            stage = ReleaseStage.CANARY
        else:
            stage = ReleaseStage.DEV

        result = ReleaseGateResult(
            id=new_id("release"),
            stage=stage,
            passed=not blockers,
            score=score,
            gates=gates,
            blockers=blockers,
        )
        self.store.append(dataclass_to_dict(result))
        return result
