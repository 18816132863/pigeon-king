"""V10 Self-Evolving Personal Operating Agent orchestrator."""

from __future__ import annotations

from typing import Any

from core.autonomy import GoalStrategyKernel, TaskGraphCompiler
from governance.codex import JudgementEngine
from memory_context.personalization import PersonalizationEngine
from infrastructure.capability_self_extension import CapabilitySelfExtensionKernel


class PersonalAutonomousOSAgent:
    def __init__(self) -> None:
        self.goal_kernel = GoalStrategyKernel()
        self.graph_compiler = TaskGraphCompiler()
        self.judgement = JudgementEngine()
        self.personalization = PersonalizationEngine()
        self.self_extension = CapabilitySelfExtensionKernel()
        self.available_capabilities = [
            "goal_modeling",
            "risk_judgement",
            "execution_graph",
            "skill_registry",
            "autonomous_execution",
        ]

    def process_goal(self, goal: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        compiled = self.goal_kernel.compile(goal, context)
        judged = self.judgement.judge(goal, context)
        graph = self.graph_compiler.compile_from_goal_model(compiled["goal"])
        required = compiled["goal"].get("required_capabilities", [])
        gaps = self.self_extension.detect_gap(required, self.available_capabilities)
        gap_plans = [self.self_extension.build_extension_plan(g, auto_mode=True) for g in gaps]
        plan = {
            "status": "ready" if judged["decision"] != "blocked" else "blocked",
            "agent_shape": "Self-Evolving Personal Operating Agent",
            "goal_compilation": compiled,
            "judgement": judged,
            "execution_graph": graph.to_dict(),
            "capability_gaps": [g.__dict__ for g in gaps],
            "capability_extension_plans": gap_plans,
            "next_action": self._next_action(judged, gaps),
        }
        return self.personalization.apply_to_plan(plan)

    @staticmethod
    def _next_action(judgement: dict[str, Any], gaps: list[Any]) -> str:
        if judgement.get("decision") == "blocked":
            return "refuse_or_request_new_goal"
        if judgement.get("requires_approval"):
            return "draft_plan_then_request_strong_confirmation"
        if gaps:
            return "resolve_capability_gaps_before_execution"
        return "execute_safe_graph_then_verify"
