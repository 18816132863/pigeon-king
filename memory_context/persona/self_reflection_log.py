"""SelfReflectionLog — 自我反思日志

每次重要任务后记录反思：
做对了什么、哪里出错、用户纠正了什么、下次怎么做。
持久化为 JSONL 文件。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

PERSONA_DIR = Path.cwd() / ".memory_persona"
PERSONA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ReflectionEntry:
    task_goal: str = ""
    what_went_right: list[str] = field(default_factory=list)
    what_went_wrong: list[str] = field(default_factory=list)
    user_corrections: list[str] = field(default_factory=list)
    next_time: list[str] = field(default_factory=list)
    should_write_to_long_term_memory: bool = False
    persona_state_impact: str = ""
    timestamp: str = ""
    task_duration_ms: int = 0
    mood_before: str = ""
    mood_after: str = ""

    def to_dict(self) -> dict:
        return {
            "task_goal": self.task_goal,
            "what_went_right": self.what_went_right,
            "what_went_wrong": self.what_went_wrong,
            "user_corrections": self.user_corrections,
            "next_time": self.next_time,
            "should_write_to_long_term_memory": self.should_write_to_long_term_memory,
            "persona_state_impact": self.persona_state_impact,
            "timestamp": self.timestamp,
            "task_duration_ms": self.task_duration_ms,
            "mood_before": self.mood_before,
            "mood_after": self.mood_after,
        }


class SelfReflectionLog:
    """自我反思日志"""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or PERSONA_DIR / "self_reflection.jsonl"
        self._entries: list[ReflectionEntry] = []
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            self._entries.append(ReflectionEntry(**data))
            except Exception:
                self._entries = []

    def add(self, entry: ReflectionEntry):
        entry.timestamp = datetime.now().isoformat()
        self._entries.append(entry)
        with open(self.storage_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def get_recent(self, n: int = 10) -> list[ReflectionEntry]:
        return sorted(self._entries, key=lambda e: e.timestamp, reverse=True)[:n]

    def get_lessons(self) -> list[str]:
        lessons = []
        for entry in self._entries:
            lessons.extend(entry.next_time)
            if entry.should_write_to_long_term_memory:
                lessons.extend(entry.what_went_right)
                lessons.extend(entry.what_went_wrong)
        return list(set(lessons))

    def get_recent_corrections(self, n: int = 5) -> list[str]:
        corrections = []
        for entry in sorted(self._entries, key=lambda e: e.timestamp, reverse=True):
            corrections.extend(entry.user_corrections)
            if len(corrections) >= n:
                break
        return corrections[:n]

    def count(self) -> int:
        return len(self._entries)


_reflection_log: Optional[SelfReflectionLog] = None


def get_self_reflection_log() -> SelfReflectionLog:
    global _reflection_log
    if _reflection_log is None:
        _reflection_log = SelfReflectionLog()
    return _reflection_log
