from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import RelationshipContext, new_id, to_dict, now_ts
from .storage import JsonStore


class RelationshipContextMap:
    """V160: relationship/context map for collaborators and channels."""

    def __init__(self, root: str | Path = ".personalization_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "relationship_contexts.json")
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if self.store.read([]):
            return
        rels = [
            RelationshipContext(new_id("rel"), "大龙虾", "technical_executor", "direct_command", "medium", ["给压缩包和一条命令，不要长篇解释"]),
            RelationshipContext(new_id("rel"), "直播运营团队", "commerce_operator", "brief_actionable", "medium", ["给卖点、话术、执行清单"]),
        ]
        self.store.write([to_dict(r) for r in rels])

    def match(self, goal: str) -> List[RelationshipContext]:
        out = []
        for item in self.store.read([]):
            r = self._from_dict(item)
            if r.name in goal or (r.role == "technical_executor" and any(x in goal for x in ["压缩包", "命令", "覆盖", "版本"])):
                out.append(r)
        return out

    def _from_dict(self, item: Dict) -> RelationshipContext:
        return RelationshipContext(
            id=item["id"],
            name=item["name"],
            role=item.get("role", ""),
            tone=item.get("tone", ""),
            trust_level=item.get("trust_level", "medium"),
            notes=list(item.get("notes", [])),
            updated_at=float(item.get("updated_at", now_ts())),
        )
