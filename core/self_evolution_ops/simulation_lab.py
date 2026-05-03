from __future__ import annotations

from typing import List
from .schemas import SimulationResult, SimulationStatus, new_id


class SimulationLab:
    """V113: dry-run simulation before real execution."""

    def simulate(self, scenario: str, planned_steps: List[str], risk_flags: List[str] | None = None) -> SimulationResult:
        risk_flags = risk_flags or []
        failures: List[str] = []
        recommendations: List[str] = []

        if not planned_steps:
            failures.append("empty_plan")
            recommendations.append("compile a task graph before execution")
        if any(x in risk_flags for x in ["secret", "payment", "external_send"]) and not any("approval" in s.lower() or "审批" in s for s in planned_steps):
            failures.append("missing_approval_gate")
            recommendations.append("insert approval interrupt before external or sensitive action")
        if len(planned_steps) > 20:
            recommendations.append("split plan into staged execution batches")

        if failures:
            status = SimulationStatus.FAIL
            score = 0.35
        elif recommendations:
            status = SimulationStatus.WARN
            score = 0.72
        else:
            status = SimulationStatus.PASS
            score = 0.93

        return SimulationResult(
            id=new_id("sim"),
            scenario=scenario,
            status=status,
            score=score,
            failures=failures,
            recommendations=recommendations,
        )
