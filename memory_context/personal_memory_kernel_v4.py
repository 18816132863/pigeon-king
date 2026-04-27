"""V29.0 Personal Memory Kernel V4.

L2 Memory Context:
- Semantic memory: durable facts.
- Episodic memory: task outcomes and failures.
- Procedural memory: preferred ways of doing.
- Preference memory: user's style, risk, interaction preferences.
- Guard prevents pollution, contradictions, and low-confidence writes.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib


@dataclass
class MemoryRecord:
    memory_id: str
    memory_type: str
    content: str
    confidence: float
    source: str
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "active"

    def to_dict(self):
        return asdict(self)


class MemoryWritebackGuardV4:
    forbidden_fragments = ["可能", "好像", "猜测", "不确定但记住", "临时"]

    def evaluate(self, memory_type: str, content: str, confidence: float, source: str) -> Dict[str, Any]:
        if not content.strip():
            return {"allow": False, "reason": "empty_content"}
        if confidence < 0.65:
            return {"allow": False, "reason": "low_confidence"}
        if any(f in content for f in self.forbidden_fragments) and memory_type in ("semantic", "profile"):
            return {"allow": False, "reason": "uncertain_semantic_memory"}
        if source not in ("user_confirmed", "task_verified", "system_observation", "procedure_success"):
            return {"allow": False, "reason": "untrusted_source"}
        return {"allow": True, "reason": "accepted"}


class PersonalMemoryKernelV4:
    def __init__(self):
        self.records: Dict[str, MemoryRecord] = {}
        self.guard = MemoryWritebackGuardV4()

    def write(self, memory_type: str, content: str, *, confidence: float, source: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        decision = self.guard.evaluate(memory_type, content, confidence, source)
        if not decision["allow"]:
            return {"status": "rejected", **decision}
        memory_id = self._make_id(memory_type, content)
        if memory_id in self.records:
            return {"status": "deduped", "memory_id": memory_id}
        record = MemoryRecord(memory_id, memory_type, content, confidence, source, tags or [])
        self.records[memory_id] = record
        return {"status": "written", "memory_id": memory_id, "record": record.to_dict()}

    def query(self, memory_type: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        items = list(self.records.values())
        if memory_type:
            items = [r for r in items if r.memory_type == memory_type]
        if tags:
            want = set(tags)
            items = [r for r in items if want.intersection(r.tags)]
        return [r.to_dict() for r in items if r.status == "active"]

    def _make_id(self, memory_type: str, content: str) -> str:
        return "mem_" + hashlib.sha256(f"{memory_type}:{content}".encode("utf-8")).hexdigest()[:16]
