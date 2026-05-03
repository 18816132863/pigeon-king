from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
from .schemas import ContextPack, new_id


class ContextFusionEngine:
    """V108: selects minimal relevant context and avoids context bloat."""

    def __init__(self, max_items: int = 8, max_token_estimate: int = 6000):
        self.max_items = max_items
        self.max_token_estimate = max_token_estimate

    def build_pack(self, goal: str, candidates: List[Dict[str, Any]] | None = None) -> ContextPack:
        candidates = candidates or self._default_candidates(goal)
        scored = []
        lower_goal = goal.lower()
        for item in candidates:
            text = f"{item.get('title','')} {item.get('content','')} {' '.join(item.get('tags', []))}".lower()
            score = 0
            for token in set(lower_goal.replace("，", " ").replace(",", " ").split()):
                if token and token in text:
                    score += 1
            if any(k in text for k in ["v85", "v86", "v87", "v97", "模型", "自治", "法典", "记忆"]):
                score += 2
            scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        selected = [x for s, x in scored[: self.max_items] if s > 0 or not goal]
        if not selected:
            selected = candidates[: min(3, len(candidates))]

        token_estimate = min(self.max_token_estimate, sum(len(str(x)) // 2 for x in selected))
        omitted = [x.get("title", "untitled") for _, x in scored[len(selected):]]
        confidence = min(0.98, 0.55 + 0.07 * len(selected))

        return ContextPack(
            id=new_id("ctx"),
            goal=goal,
            selected_context=selected,
            omitted_context=omitted,
            confidence=round(confidence, 4),
            token_estimate=token_estimate,
        )

    def _default_candidates(self, goal: str) -> List[Dict[str, Any]]:
        return [
            {"title": "V85 model routing", "content": "model decision engine and llm gateway", "tags": ["model", "router"]},
            {"title": "V86 personal execution agent", "content": "goal compiler task graph policy judge durable state", "tags": ["agent", "task_graph"]},
            {"title": "V87-V96 autonomy kernel", "content": "memory world interface capability gap sandbox approval trace quality strategy continuous task orchestrator", "tags": ["autonomy"]},
            {"title": "V97-V106 operating governance", "content": "constitution permission vault connector catalog mcp plugin sandbox handoff recovery benchmark release gate", "tags": ["governance"]},
        ]
