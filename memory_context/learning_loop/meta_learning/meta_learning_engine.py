from __future__ import annotations

from .evaluation_memory import EvaluationMemory
from .prompt_strategy_optimizer import PromptStrategyOptimizer


class MetaLearningEngine:
    """Learn how to learn better from outcomes and user correction."""

    def __init__(self) -> None:
        self.memory = EvaluationMemory()
        self.optimizer = PromptStrategyOptimizer()

    def improve(self, evaluation: dict, user_style: dict) -> dict:
        stored = self.memory.add(evaluation)
        strategy = self.optimizer.optimize(user_style)
        return {
            "status": "meta_learning_ready",
            "stored": stored,
            "strategy": strategy,
            "next_run_adjustment": "prefer_direct_complete_artifact" if user_style.get("directness") == "high" else "standard",
        }
