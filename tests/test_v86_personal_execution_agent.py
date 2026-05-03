# -*- coding: utf-8 -*-
from core.personal_agent import GoalCompiler, PersonalExecutionAgent, PolicyJudge, RiskLevel, NodeStatus


def test_v86_goal_compile_creates_goal_spec():
    goal = GoalCompiler().compile("帮我把一句话变成任务图并自动推进")
    assert goal.goal_id.startswith("goal_")
    assert goal.objectives
    assert "task_graph_created" in goal.success_criteria


def test_v86_policy_blocks_high_risk_without_approval():
    decision = PolicyJudge().decide({"action": "overwrite", "risk_hints": ["system_change"]})
    assert decision.risk_level == RiskLevel.L4
    assert decision.strong_approval_required is True


def test_v86_agent_blocks_high_risk_and_writes_experience(tmp_path):
    agent = PersonalExecutionAgent(state_root=str(tmp_path / "state"))
    result = agent.run("直接覆盖系统核心文件并删除旧逻辑")
    assert result["plan"]["approval_nodes"]
    assert any(n["status"] == NodeStatus.BLOCKED_APPROVAL.value for n in result["graph"]["nodes"])
    assert result["experience"]["reusable_procedure"]


def test_v86_agent_low_risk_progresses(tmp_path):
    agent = PersonalExecutionAgent(state_root=str(tmp_path / "state"))
    result = agent.run("帮我整理成执行计划")
    assert result["verification"]["score"] > 0
    assert result["execution_summary"]["statuses"].get("completed", 0) >= 1
