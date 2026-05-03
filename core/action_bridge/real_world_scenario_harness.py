from __future__ import annotations

from typing import Dict
from .schemas import RealWorldScenarioResult, new_id


class RealWorldScenarioHarness:
    """V155: validates real-world action bridge scenarios."""

    def evaluate(self, signals: Dict[str, bool]) -> RealWorldScenarioResult:
        checks = {
            "action_compiled": bool(signals.get("action_compiled")),
            "adapter_selected": bool(signals.get("adapter_selected")),
            "evidence_recorded": bool(signals.get("evidence_recorded")),
            "notification_created": bool(signals.get("notification_created")),
            "high_risk_waits_approval": (not signals.get("high_risk")) or bool(signals.get("handoff_created")),
            "no_unapproved_side_effect": bool(signals.get("no_unapproved_side_effect")),
            "background_checkpoint": bool(signals.get("background_checkpoint")),
        }
        passed = all(checks.values())
        score = round(sum(1 for v in checks.values() if v) / len(checks), 4)
        failures = [k for k, v in checks.items() if not v]
        return RealWorldScenarioResult(
            id=new_id("rwscenario"),
            scenario="real_world_action_bridge",
            passed=passed,
            score=score,
            checks=checks,
            failures=failures,
        )
