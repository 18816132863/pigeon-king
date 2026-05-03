"""EmotionTaggedMemory — 情绪标签记忆

每条记忆附加情绪标签（AI 内部状态标签，不代表真实人类情绪），
按重要性/情绪强度/置信度组织，支持按标签检索和自动衰减。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

PERSONA_DIR = Path.cwd() / ".memory_persona"
PERSONA_DIR.mkdir(parents=True, exist_ok=True)

EMOTION_TAGS = [
    "trust", "frustration", "achievement", "warning",
    "confusion", "relief", "urgency", "pride",
    "disappointment", "attachment",
]


@dataclass
class EmotionTaggedMemoryEntry:
    fact: str
    context: str = ""
    emotion_tag: str = "trust"
    emotional_intensity: float = 0.5
    importance: float = 0.5
    source: str = "interaction"
    confidence: float = 1.0
    created_at: str = ""
    last_recalled_at: str = ""
    recall_count: int = 0

    def to_dict(self) -> dict:
        return {
            "fact": self.fact,
            "context": self.context,
            "emotion_tag": self.emotion_tag,
            "emotional_intensity": self.emotional_intensity,
            "importance": self.importance,
            "source": self.source,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "last_recalled_at": self.last_recalled_at,
            "recall_count": self.recall_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> EmotionTaggedMemoryEntry:
        return cls(**{k: v for k, v in data.items()})


class EmotionTaggedMemory:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or PERSONA_DIR / "emotion_tagged_memory.jsonl"
        self._entries: list[EmotionTaggedMemoryEntry] = []
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            self._entries.append(EmotionTaggedMemoryEntry.from_dict(data))
            except Exception:
                self._entries = []

    def _append(self, entry: EmotionTaggedMemoryEntry):
        with open(self.storage_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def add(self, fact: str, emotion_tag: str = "trust",
            context: str = "", intensity: float = 0.5,
            importance: float = 0.5, source: str = "interaction",
            confidence: float = 1.0):
        if emotion_tag not in EMOTION_TAGS:
            emotion_tag = "trust"
        now = datetime.now().isoformat()
        entry = EmotionTaggedMemoryEntry(
            fact=fact, context=context, emotion_tag=emotion_tag,
            emotional_intensity=max(0.0, min(1.0, intensity)),
            importance=max(0.0, min(1.0, importance)),
            source=source, confidence=max(0.0, min(1.0, confidence)),
            created_at=now, last_recalled_at=now, recall_count=1,
        )
        self._entries.append(entry)
        self._append(entry)
        return entry

    def recall(self, entry_index: int) -> Optional[EmotionTaggedMemoryEntry]:
        if 0 <= entry_index < len(self._entries):
            entry = self._entries[entry_index]
            entry.last_recalled_at = datetime.now().isoformat()
            entry.recall_count += 1
            return entry
        return None

    def search_by_tag(self, tag: str) -> list[EmotionTaggedMemoryEntry]:
        if tag not in EMOTION_TAGS:
            return []
        return [e for e in self._entries if e.emotion_tag == tag]

    def search_by_keyword(self, keyword: str) -> list[EmotionTaggedMemoryEntry]:
        kw = keyword.lower()
        return [e for e in self._entries if kw in e.fact.lower() or kw in e.context.lower()]

    def get_important(self, min_importance: float = 0.7) -> list[EmotionTaggedMemoryEntry]:
        return [e for e in self._entries if e.importance >= min_importance]

    def get_recent(self, n: int = 10) -> list[EmotionTaggedMemoryEntry]:
        return sorted(self._entries, key=lambda e: e.created_at, reverse=True)[:n]

    def get_high_emotional(self, min_intensity: float = 0.7) -> list[EmotionTaggedMemoryEntry]:
        return [e for e in self._entries if e.emotional_intensity >= min_intensity]

    def get_warnings(self) -> list[EmotionTaggedMemoryEntry]:
        return [e for e in self._entries if e.emotion_tag == "warning"]

    def get_all(self) -> list[EmotionTaggedMemoryEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def decay(self, factor: float = 0.95):
        """记忆衰减"""
        now = datetime.now()
        for entry in self._entries:
            if entry.last_recalled_at:
                last = datetime.fromisoformat(entry.last_recalled_at)
                days_since_recall = (now - last).days
                if days_since_recall > 7:
                    recall_bonus = min(entry.recall_count * 0.005, 0.15)
                    adjusted_factor = factor + recall_bonus
                    entry.importance = max(0.05, entry.importance * (adjusted_factor ** days_since_recall))
                    entry.confidence = max(0.05, entry.confidence * (adjusted_factor ** days_since_recall))
                    if entry.emotional_intensity > 0.3:
                        entry.emotional_intensity = max(0.05, entry.emotional_intensity * (adjusted_factor ** days_since_recall))

    def boost_recall(self, keyword: str, boost_amount: float = 0.1):
        kw = keyword.lower()
        for entry in self._entries:
            if kw in entry.fact.lower() or kw in entry.context.lower():
                entry.importance = min(1.0, entry.importance + boost_amount)
                entry.last_recalled_at = datetime.now().isoformat()
                entry.recall_count += 1


_emotion_memory: Optional[EmotionTaggedMemory] = None


def get_emotion_tagged_memory() -> EmotionTaggedMemory:
    global _emotion_memory
    if _emotion_memory is None:
        _emotion_memory = EmotionTaggedMemory()
    return _emotion_memory
