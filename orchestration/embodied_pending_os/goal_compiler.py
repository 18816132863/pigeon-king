"""Goal compiler for the embodied-pending-access operating agent."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping

from governance.embodied_pending_state import classify_action_semantics


@dataclass
class CompiledStep:
    step_id: str
    title: str
    action: Dict[str, Any]
    semantic: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CompiledGoal:
    goal: str
    constraints: Dict[str, Any]
    steps: List[CompiledStep] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["steps"] = [s.to_dict() for s in self.steps]
        return data


class PendingGoalCompiler:
    def compile(self, goal: str, context: Mapping[str, Any] | None = None) -> CompiledGoal:
        context = dict(context or {})
        requested_actions = context.get("actions") or []
        if not requested_actions:
            requested_actions = [
                {"op_name": "analyze_goal", "summary": goal},
                {"op_name": "prepare_execution_plan", "summary": goal},
                {"op_name": "dry_run_action", "summary": goal},
            ]
        steps: List[CompiledStep] = []
        for idx, action in enumerate(requested_actions, start=1):
            semantic = classify_action_semantics(action).to_dict()
            steps.append(CompiledStep(f"step_{idx:03d}", str(action.get("summary") or action.get("op_name") or "action"), dict(action), semantic))
        return CompiledGoal(
            goal=goal,
            constraints={
                "mode": "embodied_pending_access",
                "real_world_live_access": False,
                "payment_signature_physical_actions": "hard_cutoff",
                "external_send": "draft_or_pending_outbox_only",
            },
            steps=steps,
        )
