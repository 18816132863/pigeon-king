from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import NotificationRecord, NotificationLevel, new_id, to_dict
from .storage import JsonStore


class NotificationCenter:
    """V152: durable notification center."""

    def __init__(self, root: str | Path = ".action_bridge_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "notifications.json")

    def notify(self, level: NotificationLevel, title: str, message: str, action_required: bool = False) -> NotificationRecord:
        rec = NotificationRecord(
            id=new_id("notify"),
            level=level,
            title=title,
            message=message,
            action_required=action_required,
        )
        self.store.append(to_dict(rec))
        return rec

    def list_all(self) -> List[NotificationRecord]:
        return [self._from_dict(x) for x in self.store.read([])]

    def _from_dict(self, item: Dict) -> NotificationRecord:
        return NotificationRecord(
            id=item["id"],
            level=NotificationLevel(item["level"]),
            title=item["title"],
            message=item["message"],
            action_required=bool(item.get("action_required", False)),
            created_at=float(item.get("created_at", 0.0)),
        )
