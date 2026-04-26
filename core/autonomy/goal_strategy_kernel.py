"""V10 Goal-Strategy Kernel.

Turns a one-sentence user goal into a governed objective model and execution graph.
This is deliberately deterministic and side-effect-free: real execution is delegated to
route/capability layers after governance approval.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GoalModel:
    raw_goal: str
    objective: str
    constraints: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)
    risk_hints: list[str] = field(default_factory=list)
    autonomy_level: str = "bounded_autonomy"


@dataclass
class StrategyOption:
    name: str
    priority: int
    expected_value: float
    risk_level: str
    requires_approval: bool
    steps: list[str]


class GoalStrategyKernel:
    """Goal modeling + strategy selection for the personal autonomous agent."""

    DEFAULT_SUCCESS = (
        "goal_understood",
        "risk_checked",
        "capabilities_resolved_or_gap_reported",
        "execution_graph_ready",
    )

    def model_goal(self, goal: str, context: dict[str, Any] | None = None) -> GoalModel:
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("goal must be a non-empty string")
        context = context or {}
        text = goal.strip()
        required = self._infer_required_capabilities(text)
        risk_hints = self._infer_risk_hints(text)
        constraints = list(context.get("constraints", []))
        if "不要问" in text or "自动" in text or "一句话" in text:
            constraints.append("minimize_follow_up_questions")
        if "像我" in text or "我的风格" in text:
            constraints.append("use_personalization_profile")
        return GoalModel(
            raw_goal=text,
            objective=text,
            constraints=constraints,
            success_criteria=list(self.DEFAULT_SUCCESS),
            required_capabilities=required,
            risk_hints=risk_hints,
            autonomy_level=context.get("autonomy_level", "bounded_autonomy"),
        )

    def generate_strategies(self, model: GoalModel) -> list[StrategyOption]:
        base_steps = [
            "compile_goal_tree",
            "judge_risk_and_rules",
            "resolve_capabilities",
            "build_execution_graph",
            "run_safe_steps",
            "pause_for_approval_on_high_risk",
            "verify_result_and_learn",
        ]
        conservative = StrategyOption(
            name="safe_first",
            priority=1,
            expected_value=0.72,
            risk_level="L1",
            requires_approval=False,
            steps=base_steps,
        )
        balanced = StrategyOption(
            name="personal_autonomy_balanced",
            priority=2,
            expected_value=0.86,
            risk_level="L2",
            requires_approval=bool(model.risk_hints),
            steps=base_steps + ["use_personal_style_model", "auto_recover_failures"],
        )
        self_extending = StrategyOption(
            name="self_extending_if_gap",
            priority=3,
            expected_value=0.91,
            risk_level="L3" if model.risk_hints else "L2",
            requires_approval=True,
            steps=base_steps + ["detect_capability_gap", "search_solution", "sandbox_new_capability"],
        )
        return [conservative, balanced, self_extending]

    def choose_strategy(self, model: GoalModel, strategies: list[StrategyOption]) -> StrategyOption:
        if not strategies:
            raise ValueError("strategies must not be empty")
        if model.risk_hints:
            return sorted(strategies, key=lambda s: (s.requires_approval, -s.expected_value))[0]
        return sorted(strategies, key=lambda s: (-s.expected_value, s.priority))[0]

    def compile(self, goal: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        model = self.model_goal(goal, context)
        strategies = self.generate_strategies(model)
        chosen = self.choose_strategy(model, strategies)
        return {
            "status": "compiled",
            "agent_type": "self_evolving_personal_operating_agent",
            "goal": model.__dict__,
            "chosen_strategy": chosen.__dict__,
            "alternatives": [s.__dict__ for s in strategies],
        }

    @staticmethod
    def _infer_required_capabilities(text: str) -> list[str]:
        capabilities = ["goal_modeling", "risk_judgement", "execution_graph"]
        rules = [
            ("邮件", "email_access"),
            ("日程", "calendar_access"),
            ("手机", "device_operation"),
            ("查找", "solution_search"),
            ("搜索", "solution_search"),
            ("安装", "capability_extension"),
            ("技能", "skill_registry"),
            ("外部", "external_capability_bus"),
            ("API", "external_capability_bus"),
            ("像我", "personalization_memory"),
            ("自动", "autonomous_execution"),
        ]
        for keyword, capability in rules:
            if keyword.lower() in text.lower() and capability not in capabilities:
                capabilities.append(capability)
        return capabilities

    @staticmethod
    def _infer_risk_hints(text: str) -> list[str]:
        risk_hints = []
        for keyword in ("支付", "转账", "删除", "发给", "安装", "账号", "密码", "隐私", "群发", "交易"):
            if keyword in text:
                risk_hints.append(keyword)
        return risk_hints
