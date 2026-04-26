from __future__ import annotations

from typing import Any

from .decision_cycle import DecisionCycle
from .goal_memory import GoalMemory
from .priority_scheduler import PriorityScheduler
from .runtime_state_machine import RuntimeStateMachine


class AutonomousRuntimeKernel:
    """V10.2 bounded autonomous runtime loop.

    This is the system's always-on decision spine:
    accept goal → run decision cycle → schedule tasks → gate execution → define verification/learning.
    """

    def __init__(self) -> None:
        self.decision_cycle = DecisionCycle()
        self.goal_memory = GoalMemory()
        self.scheduler = PriorityScheduler()
        self.state_machine = RuntimeStateMachine()

    def process(self, goal: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        self.state_machine.transition("observing")
        self.state_machine.transition("planning")
        cycle = self.decision_cycle.run(goal, context)
        self.goal_memory.add(goal, status="planned", priority=50, risk_level=cycle.risk_level)
        scheduled = self.scheduler.schedule([
            {**step, "task_id": f"runtime_step_{idx}", "risk_level": cycle.risk_level}
            for idx, step in enumerate(cycle.action_plan)
        ])
        if cycle.requires_confirmation:
            self.state_machine.transition("waiting_confirmation")
            next_state = "waiting_for_strong_confirmation"
        elif cycle.risk_level == "BLOCKED":
            self.state_machine.transition("blocked")
            next_state = "blocked"
        else:
            self.state_machine.transition("executing")
            next_state = "execution_ready"

        return {
            "status": "runtime_plan_ready",
            "agent_shape": "Self-Evolving Personal Operating Agent",
            "runtime_shape": "Bounded Autonomous Runtime Loop",
            "decision_cycle": cycle.to_dict(),
            "scheduled_tasks": [task.__dict__ for task in scheduled],
            "current_state": self.state_machine.state,
            "next_state": next_state,
            "memory_preview": self.goal_memory.recent(),
            "safety": {
                "strong_confirmation_required": cycle.requires_confirmation,
                "blocked_if_policy_violation": True,
                "no_untrusted_auto_install": True,
                "audit_required": True,
                "rollback_required": True,
            },
        }
