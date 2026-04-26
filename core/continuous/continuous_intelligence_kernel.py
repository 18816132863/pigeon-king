from __future__ import annotations

from .attention_manager import AttentionManager
from .runtime_budget_manager import RuntimeBudgetManager
from .context_refresh_planner import ContextRefreshPlanner
from .initiative_engine import InitiativeEngine


class ContinuousIntelligenceKernel:
    """V10.5 always-on intelligence layer.

    It does not execute external actions by itself; it decides what to observe,
    when to refresh context, and what initiative should be prepared next.
    """

    def __init__(self) -> None:
        self.attention = AttentionManager()
        self.budget = RuntimeBudgetManager()
        self.refresh = ContextRefreshPlanner()
        self.initiative = InitiativeEngine()

    def tick(self, goal: str = "", signals: list[dict] | None = None, mode: str = "bounded_high") -> dict:
        budget = self.budget.allocate(mode)
        attention = self.attention.rank(signals or [])
        refresh = self.refresh.plan(goal)
        initiatives = self.initiative.propose(attention, budget)
        return {
            "status": "continuous_tick_ready",
            "shape": "Continuous Intelligence Kernel",
            "budget": budget,
            "attention": attention,
            "context_refresh": refresh,
            "initiatives": initiatives,
            "external_side_effect": False,
            "next_decision": "prepare_initiative" if initiatives["initiatives"] else "idle",
        }
