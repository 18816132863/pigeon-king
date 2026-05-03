from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .schemas import RealWorkRequest, new_id, to_dict
from .storage import JsonStore


class RealWorkMessageEntry:
    """Normalizes every received message into a real-work request."""

    def __init__(self, root: str | Path = ".real_work_entry_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "requests.json")

    def receive(self, message: str, source: str = "chat", user_id: str = "default_user", metadata: Dict[str, Any] | None = None) -> RealWorkRequest:
        req = RealWorkRequest(
            id=new_id("rwreq"),
            message=message.strip(),
            source=source,
            user_id=user_id,
            metadata=metadata or {},
        )
        self.store.append(to_dict(req))
        return req
