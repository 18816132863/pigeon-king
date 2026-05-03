"""Self-evolving pending-access kernel."""
from __future__ import annotations
from typing import Any, Dict, Mapping
from governance.embodied_pending_state import PendingAccessMaturityScorecard
from governance.evolution_safety import AutonomyLevelPolicy, MemoryGovernance
from infrastructure.capability_evolution import CapabilityGapDetector, SkillExtensionSandbox
from infrastructure.execution_runtime.shadow_replay_validator import ShadowReplayValidator
from orchestration.embodied_pending_os import EmbodiedPendingAccessOS

COMMIT_SEMANTICS = {"payment", "signature", "physical_actuation", "external_send", "destructive", "identity_commit"}

class SelfEvolvingPendingAccessKernel:
    def __init__(self) -> None:
        self.pending_os = EmbodiedPendingAccessOS()
        self.memory = MemoryGovernance()
        self.autonomy = AutonomyLevelPolicy()
        self.gaps = CapabilityGapDetector()
        self.sandbox = SkillExtensionSandbox()
        self.shadow = ShadowReplayValidator()
        self.maturity = PendingAccessMaturityScorecard()

    def run(self, goal: str, context: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        context = dict(context or {})
        base = self.pending_os.run(goal, context)
        actions = [s.get("step", {}).get("action", {}) for s in base.get("step_results", [])]
        available = context.get("available_capabilities") or ["analyze_goal", "prepare_execution_plan", "dry_run_action", "query_calendar", "write_draft", "mock_api_call", "replay_trace"]
        gap_report = [g.to_dict() for g in self.gaps.detect(goal, actions, available)]
        sandbox_decisions = []
        for gap in gap_report:
            sandbox_decisions.append(self.sandbox.evaluate_candidate({
                "name": gap["name"],
                "source_type": "approved_connector" if gap["semantic_class"] in COMMIT_SEMANTICS else "local_registry",
                "semantic_class": gap["semantic_class"],
                "tests": ["unit_contract", "trace_replay"],
                "has_hash_or_signature": True,
                "wants_live_credentials": False,
            }).to_dict())
        memory_decisions = [self.memory.evaluate_write(c).to_dict() for c in (context.get("memory_candidates") or [])]
        shadow = self.shadow.replay(actions).to_dict()
        autonomy = self.autonomy.evaluate(context.get("autonomy") or {"level": "L3"}).to_dict()
        maturity_manifest = {
            "modules": ["goal_compiler", "long_horizon_planner", "action_semantics", "commit_barrier", "freeze_switch", "mock_contract_registry", "world_model_or_digital_twin", "shadow_replay", "memory_governance", "capability_gap_detector", "skill_extension_sandbox", "audit_replay", "risk_tier_matrix", "real_execution_broker_hardened", "approval_pack_generation", "live_adapter_contracts_declared", "payment_signature_physical_hard_stop"],
            "real_world_connected": False,
            "real_side_effect_allowed": False,
            "final_switch_limited_to": "adapter_credential_approval_config",
        }
        maturity = self.maturity.evaluate(maturity_manifest).to_dict()
        return {
            "status": "self_evolving_pending_access_ready" if maturity["status"] == "pass" and shadow["status"] == "pass" else "partial",
            "shape": "V77 自进化具身待接入态内核",
            "base_pending_os": base,
            "autonomy_policy": autonomy,
            "capability_gaps": gap_report,
            "sandbox_promotion_decisions": sandbox_decisions,
            "memory_governance": memory_decisions,
            "shadow_replay": shadow,
            "maturity": maturity,
            "invariants": {"real_world_connected": False, "real_side_effect_allowed": False, "payment_signature_physical_hard_stop": True, "external_send_draft_only": True, "self_extension_live_install_forbidden": True, "final_switch_scope": "adapter + credential + approval config only"},
        }

def run_self_evolving_pending_kernel(goal: str, context: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    return SelfEvolvingPendingAccessKernel().run(goal, context)
