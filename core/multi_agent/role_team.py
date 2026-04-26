from __future__ import annotations

from .critic_agent import CriticAgent
from .verifier_agent import VerifierAgent
from .executor_agent import ExecutorAgent


class RoleTeam:
    """Planner + critic + verifier + executor readiness team."""

    def __init__(self) -> None:
        self.critic = CriticAgent()
        self.verifier = VerifierAgent()
        self.executor = ExecutorAgent()

    def review(self, plan: dict) -> dict:
        critique = self.critic.critique(plan)
        verification = self.verifier.verify_plan(plan)
        execution = self.executor.prepare(plan)
        return {
            "status": "team_review_complete",
            "critique": critique,
            "verification": verification,
            "execution": execution,
            "allowed_to_execute": critique["status"] == "pass" and not execution["requires_confirmation"],
        }
