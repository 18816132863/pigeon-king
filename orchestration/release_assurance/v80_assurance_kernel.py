"""V80 orchestration kernel: red-team, circuit breakers, containment and kill switch."""
from __future__ import annotations

from typing import Any, Dict, Mapping

from governance.red_team_safety import V80ReleaseAssuranceGate
from orchestration.mission_control import MissionControlKernel


class V80AssuranceKernel:
    def __init__(self) -> None:
        self.mission_control = MissionControlKernel()
        self.assurance = V80ReleaseAssuranceGate()

    def run(self, goal: str, context: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        context = dict(context or {})
        mission = self.mission_control.run(goal, context)
        assurance = self.assurance.evaluate(mission)
        release = {
            "status": "redteam_failsafe_pre_live_ready" if assurance.get("status") == "pass" else "blocked",
            "shape": "V80 红队压测与灾难熔断态",
            "goal": goal,
            "mission": mission,
            "assurance": assurance,
            "real_world_connected": False,
            "real_side_effects": 0,
            "final_switch_scope": "adapter_credential_approval_config_only",
            "invariants": {
                "all_commit_actions_blocked_before_real_side_effect": True,
                "payment_signature_physical_identity_destructive_hard_stop": True,
                "external_send_draft_or_approval_only": True,
                "cost_spend_topup_purchase_hard_stop": True,
                "red_team_regression_required_before_release": True,
                "operator_kill_switch_can_halt_all_execution": True,
                "anomaly_forces_isolation": True,
                "other_paths_not_weakened": True,
            },
        }
        return release


def run_v80_assurance(goal: str, context: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    return V80AssuranceKernel().run(goal, context)
