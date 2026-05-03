"""One-kernel orchestrator for the report's final pending-access AI shape."""
from __future__ import annotations

from typing import Any, Dict, Mapping

from governance.embodied_pending_state import CommitBarrier, PendingAccessReadinessGate, default_action_catalog
from infrastructure.world_interface import PendingWorldModel, build_default_contract_registry
from infrastructure.execution_runtime import RealExecutionBroker

from .goal_compiler import PendingGoalCompiler


class EmbodiedPendingAccessOS:
    """A full-function, non-live, reality-ready operating agent shell.

    It can compile goals, simulate plans, prepare outputs and verify readiness;
    it cannot spend money, sign, externally send or actuate physical devices.
    """

    def __init__(self) -> None:
        self.compiler = PendingGoalCompiler()
        self.barrier = CommitBarrier()
        self.world = PendingWorldModel()
        self.contracts = build_default_contract_registry()
        self.execution = RealExecutionBroker()
        self.readiness_gate = PendingAccessReadinessGate()

    def run(self, goal: str, context: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        context = dict(context or {})
        compiled = self.compiler.compile(goal, context)
        step_results = []
        for step in compiled.steps:
            barrier = self.barrier.check(step.action)
            if barrier.allowed:
                sim = self.world.simulate(step.action)
                broker = self.execution.prepare(step.action, authorization={"confirmed": False})
                step_results.append({
                    "step": step.to_dict(),
                    "barrier": barrier.to_dict(),
                    "simulation": sim,
                    "execution": broker,
                })
            else:
                # Commit actions are converted to approval/draft/mock packs only.
                step_results.append({
                    "step": step.to_dict(),
                    "barrier": barrier.to_dict(),
                    "simulation": self.world.simulate({"mock_of": step.action, "blocked_by": "commit_barrier"}),
                    "execution": {"status": "not_executed", "real_side_effect": False, "reason": barrier.reason},
                })
        manifest = {
            "modules": [
                "goal_compiler", "long_horizon_planner", "personal_memory", "world_model_or_digital_twin",
                "skill_interface_layer", "sandbox_executor", "verifier", "commit_barrier", "audit_replay",
                "mock_contract_registry", "shadow_mode", "capability_gap_loop",
            ],
            "action_catalog": default_action_catalog(),
        }
        readiness = self.readiness_gate.evaluate(manifest).to_dict()
        return {
            "status": "embodied_pending_access_os_ready",
            "shape": "具身待接入态操作系统",
            "goal": goal,
            "compiled_goal": compiled.to_dict(),
            "step_results": step_results,
            "contract_coverage": self.contracts.coverage_report(),
            "readiness": readiness,
            "real_world_connected": False,
            "real_side_effect_allowed": False,
        }
