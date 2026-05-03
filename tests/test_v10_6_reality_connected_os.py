from __future__ import annotations

from core.reality import RealityGroundingKernel, FactStateResolver, EnvironmentCapabilityProbe, UncertaintyManager
from core.authorization import AuthorizationIntentGateway, ConsentScopeModel, ActionRiskAttestation
from core.project_autonomy import ProjectBrain
from infrastructure.tool_negotiation import ToolCapabilityNegotiator
from infrastructure.execution_runtime import RealExecutionBroker, RuntimeReplayEngine
from infrastructure.upgrade_governance import SelfUpgradeGovernor
from memory_context.learning_loop.audit_replay import AuditReplayLearner
from orchestration.reality_connected_personal_os_orchestrator import RealityConnectedPersonalOSOrchestrator


def test_reality_grounding_tracks_missing_facts() -> None:
    result = RealityGroundingKernel().ground("goal", {"assumptions": ["need:api_key"]})
    assert result["uncertainty"]["must_not_claim_success"] is True


def test_fact_state_resolver_blocks_missing() -> None:
    result = FactStateResolver().resolve([], ["need:permission"])
    assert result["can_execute_reality_bound_action"] is False


def test_environment_probe_has_no_side_effect() -> None:
    result = EnvironmentCapabilityProbe().probe([], {"adapter_loaded": False})
    assert result["side_effect"] is False


def test_uncertainty_manager_routes_missing_to_resolution() -> None:
    result = UncertaintyManager().classify({"fact_state": {"missing_facts": ["need:x"]}})
    assert result["next_action"] == "resolve_missing_facts"


def test_authorization_gateway_requires_confirm_for_send() -> None:
    result = AuthorizationIntentGateway().gate({"action_id": "x", "risk_level": "L3", "scopes": ["send"], "side_effect": True})
    assert result["status"] == "waiting_confirmation"
    assert result["can_execute_now"] is False


def test_consent_scope_model_flags_high_risk() -> None:
    assert ConsentScopeModel().evaluate(["read", "delete"])["requires_explicit_consent"] is True


def test_action_risk_attestation_side_effect_requires_confirmation() -> None:
    assert ActionRiskAttestation().attest({"risk_level": "L1", "side_effect": True})["requires_confirmation"] is True


def test_project_brain_external_goal_requires_strong_confirm() -> None:
    result = ProjectBrain().start_project("真实外部能力接入")
    assert result["review"]["strong_confirm_required"] is True


def test_tool_negotiator_finds_primary() -> None:
    result = ToolCapabilityNegotiator().negotiate("search", [{"tool_id": "t", "capabilities": ["search"]}])
    assert result["status"] == "negotiated"
    assert result["fallback_matrix"]["primary"]["tool_id"] == "t"


def test_execution_broker_dry_run_without_confirmation() -> None:
    result = RealExecutionBroker().prepare({"action_id": "x"}, None)
    # V85: commit barrier blocks by default, returns commit_barrier_blocked
    assert result["status"] in ("commit_barrier_blocked", "dry_run_only")
    assert result["real_side_effect"] is False


def test_runtime_replay_engine_counts_failures() -> None:
    result = RuntimeReplayEngine().replay([{"outcome": {"status": "failed"}}])
    assert result["failures"]


def test_upgrade_governor_requires_review_for_execution_changes() -> None:
    result = SelfUpgradeGovernor().govern("10.5", "10.6", ["core/authorization"])
    assert result["requires_user_review"] is True


def test_audit_replay_learner_derives_timeout_rule() -> None:
    result = AuditReplayLearner().learn([{"action_type": "route", "outcome": {"status": "timeout"}}])
    assert "probe_adapter_before_route" in result["prevention_rules"]["rules"]


def test_reality_connected_orchestrator_shape() -> None:
    result = RealityConnectedPersonalOSOrchestrator().run("接入真实外部能力", {"scopes": ["install"]})
    assert result["shape"] == "Reality-Connected Personal OS Agent"
    assert result["real_execution_allowed_now"] is False
