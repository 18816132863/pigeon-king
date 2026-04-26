from __future__ import annotations

from core.autonomy import GoalStrategyKernel, TaskGraphCompiler
from governance.codex import JudgementEngine
from infrastructure.capability_self_extension import CapabilitySelfExtensionKernel, CapabilityGap
from orchestration.personal_autonomous_os_agent import PersonalAutonomousOSAgent


def test_goal_strategy_kernel_compiles_one_sentence_goal() -> None:
    kernel = GoalStrategyKernel()
    compiled = kernel.compile("一句话完成任务，缺技能自动查找方案")
    assert compiled["status"] == "compiled"
    assert "solution_search" in compiled["goal"]["required_capabilities"]


def test_judgement_requires_approval_for_install() -> None:
    judgement = JudgementEngine().judge("自动安装一个新技能")
    assert judgement["requires_approval"] is True
    assert judgement["risk_level"] == "L3"


def test_task_graph_marks_self_extension_node_approval() -> None:
    graph = TaskGraphCompiler().compile_from_goal_model({
        "objective": "install skill",
        "required_capabilities": ["capability_extension"],
        "risk_hints": ["安装"],
    })
    assert any(n.node_type == "self_extension" and n.requires_approval for n in graph.nodes)


def test_capability_self_extension_builds_sandboxed_plan() -> None:
    plan = CapabilitySelfExtensionKernel().build_extension_plan(CapabilityGap("gap_x", "missing x", "x"))
    assert plan["safety_policy"]["sandbox_required"] is True
    assert plan["safety_policy"]["no_untrusted_direct_install"] is True


def test_personal_autonomous_os_agent_returns_shape() -> None:
    result = PersonalAutonomousOSAgent().process_goal("帮我一句话完成目标，没方案就自己搜索方案")
    assert result["agent_shape"] == "Self-Evolving Personal Operating Agent"
    assert result["interaction_policy"]["avoid_guessing"] is True
