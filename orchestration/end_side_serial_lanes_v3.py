"""V28.0 End-side Serial Lanes V3.

Global device serialization model:
- One device action at a time per device/session.
- Non-device local work may run separately.
- Pending verification blocks dependent device actions.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, List, Optional, Any
import hashlib
import time


@dataclass
class DeviceAction:
    action_id: str
    action_kind: str
    payload: Dict[str, Any]
    idempotency_key: str
    timeout_profile: str = "device_safe"
    verification_policy: str = "two_phase_verify"
    depends_on: List[str] = field(default_factory=list)


@dataclass
class DeviceReceipt:
    action_id: str
    status: str
    reason: str
    elapsed_ms: int
    idempotency_key: str

    def to_dict(self):
        return asdict(self)


class EndSideSerialLaneV3:
    def __init__(self, device_session_id: str = "default_device"):
        self.device_session_id = device_session_id
        self._locked = False
        self.completed_keys: set[str] = set()
        self.receipts: List[DeviceReceipt] = []
        self.pending_verify: Dict[str, DeviceReceipt] = {}

    def submit_many(self, actions: List[DeviceAction], executor: Callable[[DeviceAction], Dict[str, Any]]) -> List[DeviceReceipt]:
        receipts: List[DeviceReceipt] = []
        completed_actions = {r.action_id for r in self.receipts if r.status in ("success", "success_with_timeout_receipt", "skipped_duplicate")}
        for action in actions:
            if not all(dep in completed_actions for dep in action.depends_on):
                receipt = DeviceReceipt(action.action_id, "blocked_by_dependency", "dependency not completed", 0, action.idempotency_key)
                self.receipts.append(receipt)
                receipts.append(receipt)
                continue
            if self.pending_verify:
                receipt = DeviceReceipt(action.action_id, "blocked_by_pending_verify", "device action pending verification", 0, action.idempotency_key)
                self.receipts.append(receipt)
                receipts.append(receipt)
                continue
            receipts.append(self._run_one(action, executor))
            completed_actions = {r.action_id for r in self.receipts if r.status in ("success", "success_with_timeout_receipt", "skipped_duplicate")}
        return receipts

    def _run_one(self, action: DeviceAction, executor: Callable[[DeviceAction], Dict[str, Any]]) -> DeviceReceipt:
        if action.idempotency_key in self.completed_keys:
            receipt = DeviceReceipt(action.action_id, "skipped_duplicate", "idempotency key already completed", 0, action.idempotency_key)
            self.receipts.append(receipt)
            return receipt
        if self._locked:
            raise RuntimeError("parallel device execution detected")
        self._locked = True
        start = time.time()
        try:
            result = executor(action)
            elapsed = int((time.time() - start) * 1000)
            raw_status = result.get("status", "success")
            if raw_status == "timeout":
                receipt = DeviceReceipt(action.action_id, "timeout_pending_verify", "action timed out; verify before retry", elapsed, action.idempotency_key)
                self.pending_verify[action.action_id] = receipt
            elif raw_status == "success_with_timeout_receipt":
                receipt = DeviceReceipt(action.action_id, "success_with_timeout_receipt", "verified after timeout", elapsed, action.idempotency_key)
                self.completed_keys.add(action.idempotency_key)
            elif raw_status == "device_offline":
                receipt = DeviceReceipt(action.action_id, "device_offline", "device channel unavailable", elapsed, action.idempotency_key)
            else:
                receipt = DeviceReceipt(action.action_id, "success", "device action completed", elapsed, action.idempotency_key)
                self.completed_keys.add(action.idempotency_key)
            self.receipts.append(receipt)
            return receipt
        finally:
            self._locked = False

    def resolve_pending_verify(self, action_id: str, verified: bool) -> DeviceReceipt:
        if action_id not in self.pending_verify:
            raise KeyError(f"no pending verify for {action_id}")
        old = self.pending_verify.pop(action_id)
        status = "success_with_timeout_receipt" if verified else "failed_after_verify"
        receipt = DeviceReceipt(old.action_id, status, "pending verification resolved", 0, old.idempotency_key)
        if verified:
            self.completed_keys.add(old.idempotency_key)
        self.receipts.append(receipt)
        return receipt


def make_idempotency_key(action_kind: str, payload: Dict[str, Any]) -> str:
    import json
    body = json.dumps({"kind": action_kind, "payload": payload}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()
