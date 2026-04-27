"""V68.0 Real-time device conflict resolver.

Ensures all device-side actions remain in a single serial lane when they
share a device session. Pure local computation is not blocked.
"""
from dataclasses import dataclass, field
from typing import List, Dict

DEVICE_ACTION_TYPES = {"call_device_tool", "gui_device_action", "alarm", "calendar", "notification", "file", "settings", "app_action"}

@dataclass
class DeviceActionRequest:
    action_id: str
    action_type: str
    device_session_id: str = "default"
    depends_on: List[str] = field(default_factory=list)
    status: str = "queued"

class DeviceConflictResolver:
    layer = "L4_EXECUTION"

    def __init__(self):
        self.inflight_by_session: Dict[str, str] = {}
        self.completed: set[str] = set()
        self.pending_verify: set[str] = set()

    def is_device_action(self, action_type: str) -> bool:
        return action_type in DEVICE_ACTION_TYPES

    def can_start(self, req: DeviceActionRequest) -> bool:
        if not self.is_device_action(req.action_type):
            return True
        if any(dep in self.pending_verify for dep in req.depends_on):
            return False
        if any(dep not in self.completed for dep in req.depends_on):
            return False
        return req.device_session_id not in self.inflight_by_session

    def start(self, req: DeviceActionRequest) -> str:
        if not self.can_start(req):
            return "blocked_by_serial_lane_or_dependency"
        if self.is_device_action(req.action_type):
            self.inflight_by_session[req.device_session_id] = req.action_id
        req.status = "running"
        return "started"

    def finish(self, req: DeviceActionRequest, status: str) -> None:
        self.inflight_by_session.pop(req.device_session_id, None)
        req.status = status
        if status in {"success", "success_with_timeout_receipt"}:
            self.completed.add(req.action_id)
        if status == "timeout_pending_verify":
            self.pending_verify.add(req.action_id)

    def verify_pending(self, action_id: str, verified: bool) -> str:
        self.pending_verify.discard(action_id)
        if verified:
            self.completed.add(action_id)
            return "success_after_verify"
        return "failed_after_verify"
