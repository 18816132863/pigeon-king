from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import DeviceSession, DeviceStatus, new_id, to_dict
from .storage import JsonStore


class DeviceSessionManager:
    """V148: tracks device/application sessions."""

    def __init__(self, root: str | Path = ".action_bridge_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "device_sessions.json")
        self._ensure_default()

    def _ensure_default(self) -> None:
        if self.store.read([]):
            return
        default = DeviceSession(
            id=new_id("device"),
            device_name="local_runtime",
            status=DeviceStatus.CONNECTED,
            capabilities=["file_write", "dry_run", "artifact_package", "notification"],
            notes=["default local runtime session"],
        )
        self.store.write([to_dict(default)])

    def register(self, device_name: str, capabilities: List[str], connected: bool = True) -> DeviceSession:
        session = DeviceSession(
            id=new_id("device"),
            device_name=device_name,
            status=DeviceStatus.CONNECTED if connected else DeviceStatus.DISCONNECTED,
            capabilities=capabilities,
        )
        data = self.store.read([])
        data.append(to_dict(session))
        self.store.write(data)
        return session

    def best_for(self, capability: str) -> DeviceSession:
        sessions = [self._from_dict(x) for x in self.store.read([])]
        for s in sessions:
            if s.status == DeviceStatus.CONNECTED and capability in s.capabilities:
                return s
        for s in sessions:
            if s.status == DeviceStatus.CONNECTED:
                return s
        return sessions[0] if sessions else DeviceSession(new_id("device"), "none", DeviceStatus.DISCONNECTED, [])

    def _from_dict(self, item: Dict) -> DeviceSession:
        return DeviceSession(
            id=item["id"],
            device_name=item["device_name"],
            status=DeviceStatus(item["status"]),
            capabilities=list(item.get("capabilities", [])),
            last_seen_at=float(item.get("last_seen_at", 0.0)),
            notes=list(item.get("notes", [])),
        )
