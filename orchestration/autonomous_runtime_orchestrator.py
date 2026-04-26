from __future__ import annotations

from typing import Any

from core.runtime import AutonomousRuntimeKernel
from governance.policy import RuntimePolicyEnforcer
from infrastructure.acquisition import SolutionAcquisitionPipeline
from learning_loop.personal_model import PreferenceEvolution, DecisionStyleModel


class AutonomousRuntimeOrchestrator:
    """V10.2 orchestration entry.

    It converts one sentence into a governed runtime plan and acquisition pipeline when needed.
    """

    def __init__(self) -> None:
        self.kernel = AutonomousRuntimeKernel()
        self.policy = RuntimePolicyEnforcer()
        self.acquisition = SolutionAcquisitionPipeline()
        self.preference = PreferenceEvolution()
        self.style = DecisionStyleModel()

    def run_goal(self, goal: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        runtime_plan = self.kernel.process(goal, context)
        policy_result = self.policy.enforce(runtime_plan)
        gaps = []
        if runtime_plan["decision_cycle"]["oriented"]["needs_capability_search"]:
            gaps.append("solution_or_capability_gap")
        acquisition_plans = [self.acquisition.build_pipeline(gap) for gap in gaps]
        personal_style = self.style.infer([{"goal": goal}, context or {}])
        evolved = self.preference.evolve({}, {"success": False, "pattern": "runtime_plan_generated"})
        return {
            "status": "ready",
            "orchestrator_shape": "Autonomous Runtime Orchestrator",
            "runtime_plan": runtime_plan,
            "policy_result": policy_result,
            "acquisition_plans": acquisition_plans,
            "personal_style": personal_style,
            "preference_model_update": evolved,
            "execution_allowed_now": policy_result["status"] == "allowed",
        }
