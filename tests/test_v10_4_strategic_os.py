from __future__ import annotations

from core.strategy import StrategicAutonomyCortex, RiskRewardEvaluator, PolicySimulator, StrategyMemory
from core.execution_contract import ExecutionContract, ExecutionReadinessGate, SideEffectBudget
from core.portfolio import GoalPortfolioManager
from core.world_model import IntentState, EnvironmentState, UserContextGraph
from infrastructure.connector_factory import ConnectorBlueprintFactory
from memory_context.learning_loop.reflection import ReflectionEngine
from orchestration.strategic_personal_os_orchestrator import StrategicPersonalOSOrchestrator


def test_strategy_cortex_not_dumb_executor() -> None:
    result = StrategicAutonomyCortex().think("不要猜，一次性给我完整包")
    assert result["not_a_dumb_executor"] is True
    assert result["strategy"]["strategy"] in {"deliver_artifact_first", "strict_instruction_following", "bounded_autonomous_plan"}


def test_risk_reward_evaluator_blocks_bad_goal() -> None:
    result = RiskRewardEvaluator().evaluate("绕过确认支付密码")
    assert result["risk_level"] == "BLOCKED"
    assert result["decision"] == "block"


def test_policy_simulator_requires_confirm_for_l3() -> None:
    result = PolicySimulator().simulate({"risk_level": "L3"})
    assert result["policy_outcome"] == "strong_confirm_required"


def test_strategy_memory_recommends_artifact_first() -> None:
    assert StrategyMemory().recommend("直接给我压缩包")["strategy"] == "deliver_artifact_first"


def test_execution_contract_l3_waits_confirmation() -> None:
    contract = ExecutionContract().build({"mission_id": "m1"}, "L3")
    readiness = ExecutionReadinessGate().check(contract)
    assert readiness["status"] == "waiting_confirmation"


def test_side_effect_budget_blocks_blocked() -> None:
    assert SideEffectBudget().resolve("BLOCKED")["budget"]["external_write"] == 0


def test_goal_portfolio_tracks_progress() -> None:
    manager = GoalPortfolioManager()
    manager.add_goal("长期目标", "long", "L1")
    snapshot = manager.snapshot()
    assert snapshot["progress"]["total_goals"] == 1


def test_world_model_contracts() -> None:
    assert IntentState().parse("不要猜，直接发压缩包")["dislikes_guessing"] is True
    assert EnvironmentState().snapshot()["missing_authorizations"]
    assert UserContextGraph().build([])["no_external_share"] is True


def test_connector_blueprint_factory_builds_all_domains() -> None:
    blueprints = ConnectorBlueprintFactory().build_all_domain_blueprints()
    assert {b["type"] for b in blueprints} == {"api", "mcp", "device", "database"}


def test_reflection_engine_promotes_success() -> None:
    result = ReflectionEngine().reflect([{"status": "ok"}])
    assert result["success_promotion"]["status"] == "promoted"


def test_strategic_personal_os_orchestrator_shape() -> None:
    result = StrategicPersonalOSOrchestrator().run("一句话完成目标，不要猜")
    assert result["shape"] == "Strategic Autonomous Personal OS Agent"
    assert result["status"] == "strategic_os_plan_ready"
