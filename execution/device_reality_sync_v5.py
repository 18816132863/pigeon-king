"""V48.0 Device Reality Sync V5.

Global device action reality model. A connected device can still have action-level
timeouts. All multi-action device operations must pass through a single serial lane.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timezone

DEVICE_ACTION_TIMEOUT = "connected_but_action_timeout"
TIMEOUT_PENDING_VERIFY = "timeout_pending_verify"
SUCCESS_WITH_TIMEOUT_RECEIPT = "success_with_timeout_receipt"

@dataclass
class DeviceActionV5:
    action_id: str
    action_type: str
    payload: Dict[str, Any]
    idempotency_key: str
    timeout_profile: str = "default"
    verification_policy: str = "verify_after_execute"

@dataclass
class DeviceActionReceiptV5:
    action_id: str
    status: str
    detail: Dict[str, Any]
    created_at: str

class DeviceRealitySyncV5:
    def __init__(self) -> None:
        self._receipts: List[DeviceActionReceiptV5] = []
        self._seen_idempotency: Dict[str, DeviceActionReceiptV5] = {}
        self._busy = False

    def execute_serial(self, actions: List[DeviceActionV5], executor: Callable[[DeviceActionV5], Dict[str, Any]], verifier: Callable[[DeviceActionV5, Dict[str, Any]], bool]) -> List[DeviceActionReceiptV5]:
        receipts: List[DeviceActionReceiptV5] = []
        if self._busy:
            raise RuntimeError("device serial lane already acquired")
        self._busy = True
        try:
            for action in actions:
                if action.idempotency_key in self._seen_idempotency:
                    receipts.append(self._seen_idempotency[action.idempotency_key])
                    continue
                raw = executor(action)
                status = raw.get("status", "unknown")
                if status == "timeout":
                    verified = verifier(action, raw)
                    status = SUCCESS_WITH_TIMEOUT_RECEIPT if verified else TIMEOUT_PENDING_VERIFY
                elif status == "success":
                    verified = verifier(action, raw)
                    status = "success" if verified else "pending_verify"
                elif status == "device_offline":
                    status = "device_offline"
                receipt = DeviceActionReceiptV5(action_id=action.action_id, status=status, detail=raw, created_at=datetime.now(timezone.utc).isoformat())
                self._receipts.append(receipt)
                self._seen_idempotency[action.idempotency_key] = receipt
                receipts.append(receipt)
                if status == TIMEOUT_PENDING_VERIFY:
                    # dependent device actions must not continue after an unresolved timeout
                    break
        finally:
            self._busy = False
        return receipts

    def receipts(self) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self._receipts]
