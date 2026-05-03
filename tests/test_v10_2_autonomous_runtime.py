from __future__ import annotations

from core.runtime import AutonomousRuntimeKernel, DecisionCycle, PriorityScheduler, RuntimeStateMachine
from governance.policy import RuntimePolicyEnforcer, AutonomyLevelPolicy
from infrastructure.acquisition import SolutionAcquisitionPipeline
from memory_context.learning_loop.personal_model import PreferenceEvolution, DecisionStyleModel
from orchestration.autonomous_runtime_orchestrator import AutonomousRuntimeOrchestrator


def test_decision_cycle_detects_capability_gap() -> None:
    result = DecisionCycle().run("没技能就自动搜索方案")
    assert result.oriented["needs_capability_search"] is True
    assert any(step["step"] == "search_solution_or_capability" for step in result.action_plan)


def test_runtime_kernel_requires_confirmation_for_install() -> None:
    plan = AutonomousRuntimeKernel().process("自动安装一个外部能力")
    assert plan["safety"]["strong_confirmation_required"] is True


def test_policy_enforcer_blocks_or_confirms_high_risk() -> None:
    plan = AutonomousRuntimeKernel().process("自动安装一个外部能力")
    gate = RuntimePolicyEnforcer().enforce(plan)
    assert gate["status"] == "requires_confirmation"


def test_solution_acquisition_pipeline_never_direct_installs() -> None:
    plan = SolutionAcquisitionPipeline().build_pipeline("missing_connector")
    assert plan["safety"]["no_direct_untrusted_install"] is True
    assert plan["safety"]["sandbox_required"] is True


def test_autonomous_runtime_orchestrator_shape() -> None:
    result = AutonomousRuntimeOrchestrator().run_goal("没方案就自己搜索方案")
    assert result["orchestrator_shape"] == "Autonomous Runtime Orchestrator"
    assert result["acquisition_plans"]


def test_preference_evolution_keeps_direct_style() -> None:
    model = PreferenceEvolution().evolve({}, {"success": True, "pattern": "direct_execution"})
    assert model["preferred_style"] == "direct"


def test_decision_style_model_infers_directness() -> None:
    style = DecisionStyleModel().infer([{"text": "直接做，不要猜"}])
    assert style["directness"] == "high"


def test_runtime_state_machine_rejects_invalid_transition() -> None:
    sm = RuntimeStateMachine()
    result = sm.transition("executing")
    assert result["status"] == "rejected"


def test_autonomy_level_policy_has_bounded_high() -> None:
    policy = AutonomyLevelPolicy().resolve("bounded_high")
    assert policy["auto_search"] is True
    assert policy["auto_extend"] == "sandbox_only"
