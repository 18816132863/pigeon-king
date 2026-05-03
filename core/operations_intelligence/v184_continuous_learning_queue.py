from __future__ import annotations
from pathlib import Path
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id
from .storage import JsonStore

class ContinuousLearningQueue:
    """V184: continuous learning queue."""
    def __init__(self, root: str | Path = ".operations_intelligence_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "learning_queue.json")

    def enqueue(self, lesson: str, source: str = "runtime") -> IntelligenceArtifact:
        item = {"id": new_id("lesson"), "lesson": lesson, "source": source, "status": "queued"}
        self.store.append(item)
        return IntelligenceArtifact(new_id("learnq"), "learning_queue_item", "learning", IntelligenceStatus.LEARNING, 0.8, item)

    def count(self) -> int:
        return len(self.store.read([]))
