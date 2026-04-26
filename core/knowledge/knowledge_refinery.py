from __future__ import annotations

from .source_quality_evaluator import SourceQualityEvaluator
from .knowledge_decay_policy import KnowledgeDecayPolicy
from .solution_memory_index import SolutionMemoryIndex


class KnowledgeRefinery:
    """Turn raw search/results into reusable, quality-scored knowledge."""

    def __init__(self) -> None:
        self.quality = SourceQualityEvaluator()
        self.decay = KnowledgeDecayPolicy()
        self.index = SolutionMemoryIndex()

    def refine(self, goal: str, sources: list[dict]) -> dict:
        evaluated = [{**s, "quality": self.quality.evaluate(s), "decay": self.decay.classify(s)} for s in sources]
        accepted = [s for s in evaluated if s["quality"]["quality_score"] >= 70]
        indexed = [self.index.add_solution(goal, s) for s in accepted]
        return {
            "status": "refined",
            "accepted_count": len(accepted),
            "rejected_count": len(evaluated) - len(accepted),
            "indexed": indexed,
            "requires_refresh": any(s["decay"]["refresh_required"] for s in evaluated),
        }
