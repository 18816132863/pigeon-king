"""
V24.8 End-Side Hard Serial Gate

Global policy: in the same goal / transaction / device session, all end-side actions
must be serialized. This gate normalizes a mixed plan into a device-safe order and
detects bypass attempts from agent_kernel / task_graph / autonomous_loop.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional
import time


END_SIDE_KINDS = {
    "call_device_tool",
    "gui_device_action",
    "app_action",
    "notification",
    "alarm",
    "calendar",
    "file",
    "settings",
    "device_action",
}


@dataclass(frozen=True)
class EndSideAction:
    action_id: str
    kind: str
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)
    idempotency_key: Optional[str] = None
    timeout_profile: str = "default"
    verification_policy: str = "post_verify"
    depends_on: List[str] = field(default_factory=list)

    @property
    def is_end_side(self) -> bool:
        return self.kind in END_SIDE_KINDS or self.payload.get("end_side") is True


@dataclass
class SerialPlan:
    goal_id: str
    serial_device_actions: List[EndSideAction]
    non_device_actions: List[EndSideAction]
    barriers: List[str]
    normalized_at: float


class EndSideHardSerialGate:
    """Forces all device actions in one goal to a single-lane serial queue."""

    def normalize(self, goal_id: str, actions: Iterable[EndSideAction]) -> SerialPlan:
        device: List[EndSideAction] = []
        local: List[EndSideAction] = []
        for action in actions:
            self._validate_contract(action)
            if action.is_end_side:
                device.append(action)
            else:
                local.append(action)

        # Stable order. Dependencies are not deeply topologically sorted here because this
        # gate is intentionally simple and deterministic; dependency blocking is enforced
        # by DeviceDependencyBarrier.
        barriers = [
            "device_lock_required",
            "one_end_side_action_at_a_time",
            "verify_or_pending_verify_before_next_dependent_device_action",
        ]
        return SerialPlan(
            goal_id=goal_id,
            serial_device_actions=device,
            non_device_actions=local,
            barriers=barriers,
            normalized_at=time.time(),
        )

    def assert_no_parallel_device_actions(self, actions: Iterable[EndSideAction]) -> None:
        device_count = sum(1 for action in actions if action.is_end_side)
        if device_count > 1:
            # This does not block multi-action device plans; it blocks bypassing the
            # serial gate. Call normalize() to make it safe.
            raise RuntimeError(
                "multiple end-side actions detected; route through EndSideHardSerialGate.normalize()"
            )

    def _validate_contract(self, action: EndSideAction) -> None:
        if not action.action_id:
            raise ValueError("end-side action must have action_id")
        if action.is_end_side:
            missing = []
            if not action.idempotency_key:
                missing.append("idempotency_key")
            if not action.timeout_profile:
                missing.append("timeout_profile")
            if not action.verification_policy:
                missing.append("verification_policy")
            if missing:
                raise ValueError(f"end-side action {action.action_id} missing: {', '.join(missing)}")
