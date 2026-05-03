from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import HandoffItem, HandoffStatus, new_id, to_dict
from .storage import JsonStore


class HandoffInbox:
    """V153: human handoff inbox for approvals and decisions."""

    def __init__(self, root: str | Path = ".action_bridge_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "handoff_items.json")

    def create(self, title: str, reason: str, action_id: str, options: List[str] | None = None) -> HandoffItem:
        item = HandoffItem(
            id=new_id("handoff"),
            title=title,
            reason=reason,
            action_id=action_id,
            status=HandoffStatus.OPEN,
            options=options or ["approve", "reject", "revise"],
        )
        self.store.append(to_dict(item))
        return item

    def open_items(self) -> List[HandoffItem]:
        return [self._from_dict(x) for x in self.store.read([]) if x.get("status") == HandoffStatus.OPEN.value]

    def resolve(self, item_id: str, approve: bool) -> HandoffItem:
        data = self.store.read([])
        for item in data:
            if item["id"] == item_id:
                item["status"] = HandoffStatus.RESOLVED.value if approve else HandoffStatus.REJECTED.value
                self.store.write(data)
                return self._from_dict(item)
        raise KeyError(f"unknown handoff item: {item_id}")

    def _from_dict(self, item: Dict) -> HandoffItem:
        return HandoffItem(
            id=item["id"],
            title=item["title"],
            reason=item["reason"],
            action_id=item["action_id"],
            status=HandoffStatus(item["status"]),
            options=list(item.get("options", [])),
            created_at=float(item.get("created_at", 0.0)),
        )
