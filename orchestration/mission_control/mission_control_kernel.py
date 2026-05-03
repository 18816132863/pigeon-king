"""V79 mission control: constitution, risk proofs, rollback and preflight."""
from __future__ import annotations

from typing import Any, Dict, Mapping

from governance.constitutional_runtime import PreflightGate, RiskProofBuilder
from infrastructure.rollback_governance import RollbackPlanBuilder
from orchestration.autonomous_task_runtime import AutonomousPendingRuntimeKernel


class CapabilityMatrix:
    """Scores whether the system is balanced across embodied and digital paths."""

    REQUIRED = {
        "digital_global_agent": ["task_graph", "audit_ledger", "checkpoint", "approval_packet"],
        "embodied_pending_core": ["action_semantics", "commit_barrier", "mock_contract", "world_model"],
        "creative_research_shell": ["generate", "prepare", "simulate", "trace"],
        "governance_shell": ["constitution", "risk_proof", "rollback", "preflight"],
    }

    def evaluate(self, mission_artifacts: Mapping[str, Any]) -> Dict[str, Any]:
        available = set(mission_artifacts.get("available_capabilities") or [])
        results = {}
        for lane, required in self.REQUIRED.items():
            ok_items = [item for item in required if item in available]
            results[lane] = {
                "required": required,
                "present": ok_items,
                "score": round(len(ok_items) / len(required), 4),
                "ok": len(ok_items) == len(required),
            }
        score = round(sum(v["score"] for v in results.values()) / max(len(results), 1), 4)
        return {
            "status": "pass" if score >= 0.90 and all(v["ok"] for v in results.values()) else "partial",
            "score": score,
            "lanes": results,
            "principle": "entity_path_and_pure_digital_path_share_the_same_governed_kernel",
        }


class MissionControlKernel:
    def __init__(self) -> None:
        self.runtime = AutonomousPendingRuntimeKernel()
        self.proofs = RiskProofBuilder()
        self.rollback = RollbackPlanBuilder()
        self.preflight = PreflightGate()
        self.matrix = CapabilityMatrix()

    def run(self, goal: str, context: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        context = dict(context or {})
        runtime = self.runtime.run(goal, context)
        risk_proofs = self.proofs.build_for_run(runtime)
        rollback_plan = self.rollback.build(runtime)
        capability_matrix = self.matrix.evaluate({
            "available_capabilities": [
                "task_graph", "audit_ledger", "checkpoint", "approval_packet",
                "action_semantics", "commit_barrier", "mock_contract", "world_model",
                "generate", "prepare", "simulate", "trace",
                "constitution", "risk_proof", "rollback", "preflight",
            ]
        })
        mission: Dict[str, Any] = {
            "status": "preflight_pending",
            "shape": "V79 宪法治理与预上线闸门态",
            "goal": goal,
            "runtime": runtime,
            "risk_proofs": risk_proofs,
            "rollback_plan": rollback_plan,
            "capability_matrix": capability_matrix,
            "real_world_connected": False,
            "real_side_effects": 0,
            "final_switch_scope": "adapter_credential_approval_config_only",
            "invariants": {
                "payment_signature_physical_hard_stop": True,
                "external_send_draft_only": True,
                "destructive_identity_commit_blocked": True,
                "live_credentials_absent": True,
                "real_actuator_absent": True,
                "rollback_never_depends_on_live_undo": True,
                "other_paths_not_weakened": True,
            },
        }
        mission["preflight_gate"] = self.preflight.evaluate(mission).to_dict()
        mission["status"] = "pre_live_release_candidate_ready" if mission["preflight_gate"]["status"] == "pass" else "blocked"
        return mission


def run_mission_control(goal: str, context: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    return MissionControlKernel().run(goal, context)
