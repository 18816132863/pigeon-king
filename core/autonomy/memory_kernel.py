from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from .schemas import MemoryKind, MemoryRecord, new_id, now_ts
from .storage import JsonStore


class MemoryKernel:
    """V87: individual long-term memory kernel.

    Stores user profile, preferences, episodic memory and procedural memory.
    It is intentionally lightweight and file-backed so it can run without
    external services.
    """

    def __init__(self, root: str | Path = ".autonomy_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "memory_records.json")

    def upsert(self, kind: MemoryKind, key: str, value: Any, confidence: float = 0.7, source: str = "system", tags: Optional[List[str]] = None) -> MemoryRecord:
        tags = tags or []
        data = self.store.read([])
        for item in data:
            if item.get("kind") == kind.value and item.get("key") == key:
                item["value"] = value
                item["confidence"] = max(float(item.get("confidence", 0.0)), confidence)
                item["source"] = source
                item["updated_at"] = now_ts()
                item["tags"] = sorted(set(item.get("tags", []) + tags))
                self.store.write(data)
                return self._from_dict(item)

        rec = MemoryRecord(
            id=new_id("mem"),
            kind=kind,
            key=key,
            value=value,
            confidence=confidence,
            source=source,
            tags=tags,
        )
        data.append(rec.to_dict())
        self.store.write(data)
        return rec

    def remember_preference(self, key: str, value: Any, confidence: float = 0.8) -> MemoryRecord:
        return self.upsert(MemoryKind.PREFERENCE, key, value, confidence=confidence, source="preference_inference", tags=["preference"])

    def record_episode(self, goal: str, outcome: str, lessons: Optional[List[str]] = None) -> MemoryRecord:
        return self.upsert(
            MemoryKind.EPISODIC,
            key=f"episode::{new_id('goal')}",
            value={"goal": goal, "outcome": outcome, "lessons": lessons or []},
            confidence=0.75,
            source="execution_result",
            tags=["episode", "execution"],
        )

    def record_procedure(self, name: str, steps: List[str], success_score: float) -> MemoryRecord:
        return self.upsert(
            MemoryKind.PROCEDURAL,
            key=f"procedure::{name}",
            value={"name": name, "steps": steps, "success_score": success_score},
            confidence=min(1.0, max(0.1, success_score)),
            source="procedure_learning",
            tags=["procedure"],
        )

    def get(self, kind: MemoryKind, key: str) -> Optional[MemoryRecord]:
        for item in self.store.read([]):
            if item.get("kind") == kind.value and item.get("key") == key:
                return self._from_dict(item)
        return None

    def search(self, query: str = "", kinds: Optional[List[MemoryKind]] = None, limit: int = 20) -> List[MemoryRecord]:
        q = query.lower().strip()
        allowed = {k.value for k in kinds} if kinds else None
        out = []
        for item in self.store.read([]):
            if allowed and item.get("kind") not in allowed:
                continue
            hay = f"{item.get('key','')} {item.get('value','')} {' '.join(item.get('tags', []))}".lower()
            if not q or q in hay:
                out.append(self._from_dict(item))
        out.sort(key=lambda r: (r.confidence, r.updated_at), reverse=True)
        return out[:limit]

    def summarize_for_prompt(self) -> Dict[str, Any]:
        records = self.search(limit=100)
        prefs = [r for r in records if r.kind == MemoryKind.PREFERENCE]
        procedures = [r for r in records if r.kind == MemoryKind.PROCEDURAL]
        return {
            "preferences": {r.key: r.value for r in prefs[:20]},
            "top_procedures": [r.value for r in procedures[:10]],
            "record_count": len(records),
        }

    def _from_dict(self, item: Dict[str, Any]) -> MemoryRecord:
        item = dict(item)
        item["kind"] = MemoryKind(item["kind"])
        return MemoryRecord(**item)
