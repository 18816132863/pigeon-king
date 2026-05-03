"""ContextPriorityRouter — 上下文优先级路由

按优先级裁剪上下文：
P0 永不裁剪、P1 高优先级、P2 可裁剪。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

P0_NEVER_CUT = 0
P1_HIGH = 1
P2_CUTTABLE = 2


@dataclass
class PriorityItem:
    content: str
    priority: int
    category: str = ""
    char_count: int = 0

    def __post_init__(self):
        self.char_count = len(self.content)


class ContextPriorityRouter:
    def __init__(self, max_chars: int = 4000):
        self.max_chars = max_chars

    def route(self, items: list[PriorityItem]) -> list[PriorityItem]:
        sorted_items = sorted(items, key=lambda x: x.priority)
        p0 = [i for i in sorted_items if i.priority == P0_NEVER_CUT]
        p1 = [i for i in sorted_items if i.priority == P1_HIGH]
        p2 = [i for i in sorted_items if i.priority == P2_CUTTABLE]
        result = list(p0)
        remaining = self.max_chars - self._total_chars(result)
        for item in p1:
            if item.char_count <= remaining:
                result.append(item)
                remaining -= item.char_count
            else:
                truncated = item.content[:max(remaining - 10, 0)] + "..."
                result.append(PriorityItem(content=truncated, priority=P1_HIGH, category=item.category))
                remaining = 0
                break
        remaining = self.max_chars - self._total_chars(result)
        for item in p2:
            if item.char_count <= remaining:
                result.append(item)
                remaining -= item.char_count
            else:
                break
        return result

    def _total_chars(self, items: list[PriorityItem]) -> int:
        return sum(i.char_count for i in items)

    def classify(self, category: str) -> int:
        p0_cats = {"safety_red_line", "current_goal", "user_preference",
                    "current_project", "forbidden_action", "recent_failure", "next_step"}
        p1_cats = {"persona_state", "relationship_summary", "recent_success", "available_tool"}
        if category in p0_cats:
            return P0_NEVER_CUT
        elif category in p1_cats:
            return P1_HIGH
        return P2_CUTTABLE


_priority_router: ContextPriorityRouter | None = None


def get_context_priority_router() -> ContextPriorityRouter:
    global _priority_router
    if _priority_router is None:
        _priority_router = ContextPriorityRouter()
    return _priority_router
