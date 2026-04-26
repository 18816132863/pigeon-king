from __future__ import annotations

from core.collaboration import CollaborativeAutonomyKernel, AgentRoleRegistry, ConsensusGate
from infrastructure.mesh import MeshNodeRegistry, MeshMessageBus
from core.digital_twin import PersonalDigitalTwin, IdentityDriftGuard
from learning_loop.identity_evolution import IdentityEvolutionEngine
from core.executive_os import ExecutiveOperatingKernel, CommandIntentCompiler, OperatingModeSwitch, AutonomyMaturityScore
from core.self_governance import ConstitutionalPolicyCore, ValueAlignmentChecker, AutonomyBoundaryManager
from infrastructure.runtime_fabric import RuntimeFabricOrchestrator
from orchestration.executive_personal_os_orchestrator import ExecutivePersonalOSOrchestrator


def test_v10_7_collaboration_mesh_ready() -> None:
    result = CollaborativeAutonomyKernel().run({"objective": "goal"})
    assert result["shape"] == "Collaborative Autonomy Mesh"
    assert result["consensus"]["status"] == "consensus_ready"


def test_agent_role_registry_has_critic_and_verifier() -> None:
    roles = AgentRoleRegistry().list_roles()["roles"]
    assert "critic" in roles and "verifier" in roles


def test_consensus_gate_blocks_bad_output() -> None:
    result = ConsensusGate().decide([{"status": "blocked"}])
    assert result["requires_user_review"] is True


def test_mesh_message_bus_is_local_only() -> None:
    bus = MeshMessageBus().route("a", "b", {"x": 1})
    assert bus["external_side_effect"] is False


def test_mesh_node_registry_registers_planned_node() -> None:
    node = MeshNodeRegistry().register("n1", "agent", ["review"])
    assert node["status"] == "planned"


def test_v10_8_digital_twin_ready_and_safe() -> None:
    result = PersonalDigitalTwin().build(signals=[{"text": "直接给我压缩包"}], decisions=[{"text": "一次性"}], events=[{"x": 1}])
    assert result["shape"] == "Personal Digital Twin"
    assert result["guard"]["must_not_impersonate_user"] is True


def test_identity_drift_guard_detects_bad_claim() -> None:
    result = IdentityDriftGuard().check({"text": "I am the user"})
    assert result["status"] == "drift_detected"


def test_identity_evolution_incorporates_correction() -> None:
    result = IdentityEvolutionEngine().evolve({}, {"type": "style", "value": "direct"})
    assert result["status"] == "identity_model_evolved"


def test_v10_9_executive_kernel_ready() -> None:
    result = ExecutiveOperatingKernel().operate("一句话完成任务，没技能就找方案")
    assert result["shape"] == "Executive Personal OS Agent"
    assert result["maturity"]["score"] == 100


def test_command_intent_compiler_detects_self_extension() -> None:
    result = CommandIntentCompiler().compile("没技能就自动找方案")
    assert result["needs_self_extension"] is True


def test_operating_mode_switch_uses_safe_on_high_uncertainty() -> None:
    result = OperatingModeSwitch().select({}, {"uncertainty": {"uncertainty_level": "high"}})
    assert result["mode"] == "safe"


def test_self_governance_rules_and_alignment() -> None:
    assert "never_fake_success" in ConstitutionalPolicyCore().rules()["rules"]
    assert ValueAlignmentChecker().check({"x": "fake_success"})["status"] == "violation"
    assert AutonomyBoundaryManager().boundary("L4")["confirmation_required"] is True


def test_runtime_fabric_orchestrator_ready() -> None:
    result = RuntimeFabricOrchestrator().orchestrate([], ["a", "b"])
    assert result["status"] == "runtime_fabric_ready"


def test_executive_personal_os_orchestrator_shape() -> None:
    result = ExecutivePersonalOSOrchestrator().run("一句话完成任务，不要猜")
    assert result["shape"] == "Executive Personal OS Agent"
    assert result["status"] == "executive_personal_os_ready"
    assert result["can_claim_done"] is False
