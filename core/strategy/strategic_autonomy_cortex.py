from __future__ import annotations

from .risk_reward_evaluator import RiskRewardEvaluator
from .policy_simulator import PolicySimulator
from .strategy_memory import StrategyMemory


class StrategicAutonomyCortex:
    """V10.4 strategic brain: decide what to do, why, and under which constraints."""

    def __init__(self) -> None:
        self.evaluator = RiskRewardEvaluator()
        self.simulator = PolicySimulator()
        self.memory = StrategyMemory()

    def think(self, goal: str, context: dict | None = None) -> dict:
        recommendation = self.memory.recommend(goal)
        evaluation = self.evaluator.evaluate(goal, context or {})
        simulation = self.simulator.simulate({"risk_level": evaluation["risk_level"], "evaluation": evaluation})
        self.memory.add(goal, recommendation["strategy"], evaluation["risk_level"])
        return {
            "status": "strategy_ready",
            "strategy": recommendation,
            "evaluation": evaluation,
            "policy_simulation": simulation,
            "next_mode": "blocked" if evaluation["decision"] == "block" else "mission_orchestration",
            "not_a_dumb_executor": True,
        }
