from __future__ import annotations

from core.mission import MissionControlCenter
from core.multi_agent import RoleTeam
from core.verification import ResultVerifier, RollbackManager, AuditTrail
from infrastructure.connectors import ExternalConnectorRegistry, PermissionScopeManager, ConnectorHealthMonitor
from infrastructure.capability_acquisition import SkillDiscoveryEngine, TrustedSourcePolicy, ExtensionLifecycleManager, SandboxPromotionGate
from learning_loop.personal_evolution import PersonalFeedbackRouter, BehaviorPatternMiner, RiskToleranceCalibrator
from orchestration.proactive_personal_os_orchestrator import ProactivePersonalOSOrchestrator


def test_mission_control_builds_capability_acquisition_node() -> None:
    result = MissionControlCenter().build_mission("没技能就自己找方案")
    assert any(n["node_type"] == "capability_acquisition" for n in result["mission"]["nodes"])


def test_role_team_blocks_confirmation_plans() -> None:
    plan = {"requires_confirmation": True}
    result = RoleTeam().review(plan)
    assert result["allowed_to_execute"] is False


def test_skill_discovery_never_direct_installs_unknown() -> None:
    result = SkillDiscoveryEngine().discover("gap")
    assert all(c["policy"]["direct_install_allowed"] is False for c in result["candidates"])


def test_connector_registry_requires_authorization() -> None:
    connector = ExternalConnectorRegistry().register_planned("api", "api", ["read"])
    assert connector["requires_user_authorization"] is True


def test_permission_scope_manager_flags_high_risk() -> None:
    result = PermissionScopeManager().evaluate(["read", "send"])
    assert result["status"] == "requires_approval"


def test_verification_and_rollback_contracts() -> None:
    assert ResultVerifier().verify({}, {"status": "ready"})["success"] is True
    assert RollbackManager().build_rollback_plan([{"x": 1}])["requires_snapshot"] is True
    assert AuditTrail().build_event("x", {})["audit_required"] is True


def test_extension_lifecycle_requires_approval() -> None:
    result = ExtensionLifecycleManager().next_stage("approved", approval=False)
    assert result["status"] == "blocked"


def test_sandbox_promotion_never_active_directly() -> None:
    result = SandboxPromotionGate().evaluate({"success": True}, {"audit_required": True}, {"requires_snapshot": True})
    assert result["status"] == "promote_to_experimental"
    assert result["can_be_active"] is False


def test_personal_evolution_components() -> None:
    assert PersonalFeedbackRouter().route_feedback({"correction": True})["target"] == "decision_style_model"
    assert BehaviorPatternMiner().mine([{"text": "直接给我压缩包"}])["patterns"]["direct_execution_preference"] is True
    assert RiskToleranceCalibrator().calibrate([{"prefer": "auto"}])["high_risk_strong_confirm"] is True


def test_proactive_personal_os_orchestrator_shape() -> None:
    result = ProactivePersonalOSOrchestrator().run("没方案就自己搜索方案")
    assert result["shape"] == "Proactive Self-Extending Personal OS Agent"
    assert result["capability_discovery"] is not None
