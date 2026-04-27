"""V24.7 End-side Global Serial Executor.

All end-side actions that touch the device/app/GUI/notification/alarm/calendar/file/settings
must execute through a single-device serial lane when they belong to the same user goal,
transaction, or device session.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence
import hashlib, json, uuid

class DeviceActionState(str, Enum):
    QUEUED = 'queued'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
    TIMEOUT_PENDING_VERIFY = 'timeout_pending_verify'
    SKIPPED_DUPLICATE = 'skipped_duplicate'
    BLOCKED_BY_DEPENDENCY = 'blocked_by_dependency'

class DeviceActionType(str, Enum):
    ALARM = 'alarm'
    NOTIFICATION = 'notification'
    CALENDAR = 'calendar'
    GUI = 'gui_action'
    FILE = 'file'
    APP = 'app_action'
    SETTINGS = 'settings'
    DEVICE_TOOL = 'device_tool'

@dataclass(frozen=True)
class TimeoutProfile:
    seconds: int = 60
    timeout_state: DeviceActionState = DeviceActionState.TIMEOUT_PENDING_VERIFY

@dataclass(frozen=True)
class VerificationPolicy:
    name: str = 'verify_after_action'
    verify_after_timeout: bool = True
    allow_success_with_timeout_receipt: bool = True

@dataclass
class DeviceAction:
    action_type: str
    capability_name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    idempotency_key: Optional[str] = None
    timeout_profile: TimeoutProfile = field(default_factory=TimeoutProfile)
    verification_policy: VerificationPolicy = field(default_factory=VerificationPolicy)
    depends_on: Sequence[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    def normalized_idempotency_key(self) -> str:
        if self.idempotency_key:
            return self.idempotency_key
        payload = {'action_type': self.action_type, 'capability_name': self.capability_name, 'arguments': self.arguments}
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()

@dataclass
class DeviceActionReceipt:
    action_id: str
    action_type: str
    capability_name: str
    state: DeviceActionState
    started_at: str
    finished_at: str
    idempotency_key: str
    sequence_no: int
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    verified: bool = False
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_id': self.action_id,
            'action_type': self.action_type,
            'capability_name': self.capability_name,
            'state': self.state.value,
            'started_at': self.started_at,
            'finished_at': self.finished_at,
            'idempotency_key': self.idempotency_key,
            'sequence_no': self.sequence_no,
            'result': self.result,
            'error': self.error,
            'verified': self.verified,
        }

Backend = Callable[[DeviceAction], Dict[str, Any]]
Verifier = Callable[[DeviceAction, Dict[str, Any]], bool]

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class EndSideGlobalSerialExecutor:
    """Single-lane executor for all end-side actions in one transaction.

    Guarantees:
    - no concurrent device action execution inside this executor;
    - idempotency key dedupe before execution;
    - dependency blocking;
    - timeout is represented as timeout_pending_verify, not device_offline;
    - result verification is separated from raw tool return.
    """
    def __init__(self, *, transaction_id: Optional[str] = None, backend: Optional[Backend] = None, verifier: Optional[Verifier] = None) -> None:
        self.transaction_id = transaction_id or str(uuid.uuid4())
        self._backend = backend or self._default_backend
        self._verifier = verifier or self._default_verifier
        self._lock = Lock()
        self._lock_held = False
        self._queue: List[DeviceAction] = []
        self._receipts: List[DeviceActionReceipt] = []
        self._seen_idempotency_keys: set[str] = set()
        self._completed_action_ids: set[str] = set()
        self._sequence = 0
        self.parallel_violation_count = 0
    @staticmethod
    def _default_backend(action: DeviceAction) -> Dict[str, Any]:
        return {'ok': True, 'capability_name': action.capability_name, 'arguments': action.arguments}
    @staticmethod
    def _default_verifier(action: DeviceAction, result: Dict[str, Any]) -> bool:
        return bool(result.get('ok', False))
    def enqueue(self, action: DeviceAction) -> None:
        self._queue.append(action)
    def enqueue_many(self, actions: Iterable[DeviceAction]) -> None:
        for action in actions:
            self.enqueue(action)
    @property
    def receipts(self) -> List[DeviceActionReceipt]:
        return list(self._receipts)
    def run_all(self) -> List[DeviceActionReceipt]:
        while self._queue:
            action = self._queue.pop(0)
            receipt = self._execute_one(action)
            self._receipts.append(receipt)
            if receipt.state in (DeviceActionState.SUCCESS, DeviceActionState.TIMEOUT_PENDING_VERIFY):
                self._completed_action_ids.add(action.action_id)
        return self.receipts
    def _execute_one(self, action: DeviceAction) -> DeviceActionReceipt:
        idem = action.normalized_idempotency_key()
        started_at = _utc_now()
        if idem in self._seen_idempotency_keys:
            self._sequence += 1
            return DeviceActionReceipt(action.action_id, action.action_type, action.capability_name, DeviceActionState.SKIPPED_DUPLICATE, started_at, _utc_now(), idem, self._sequence, {'duplicate': True}, verified=True)
        missing_dependencies = [dep for dep in action.depends_on if dep not in self._completed_action_ids]
        if missing_dependencies:
            self._sequence += 1
            return DeviceActionReceipt(action.action_id, action.action_type, action.capability_name, DeviceActionState.BLOCKED_BY_DEPENDENCY, started_at, _utc_now(), idem, self._sequence, {'missing_dependencies': missing_dependencies}, 'dependency_not_completed', False)
        with self._lock:
            if self._lock_held:
                self.parallel_violation_count += 1
                self._sequence += 1
                return DeviceActionReceipt(action.action_id, action.action_type, action.capability_name, DeviceActionState.FAILED, started_at, _utc_now(), idem, self._sequence, {}, 'parallel_device_action_violation', False)
            self._lock_held = True
            try:
                raw_result = self._backend(action)
                self._sequence += 1
                if raw_result.get('timeout') is True:
                    state = action.timeout_profile.timeout_state
                    verified = False
                    if action.verification_policy.verify_after_timeout:
                        verified = bool(raw_result.get('verified_after_timeout', False))
                        if verified and action.verification_policy.allow_success_with_timeout_receipt:
                            state = DeviceActionState.SUCCESS
                    self._seen_idempotency_keys.add(idem)
                    return DeviceActionReceipt(action.action_id, action.action_type, action.capability_name, state, started_at, _utc_now(), idem, self._sequence, raw_result, None if verified else 'action_timeout_pending_verify', verified)
                verified = self._verifier(action, raw_result)
                state = DeviceActionState.SUCCESS if verified else DeviceActionState.FAILED
                self._seen_idempotency_keys.add(idem)
                return DeviceActionReceipt(action.action_id, action.action_type, action.capability_name, state, started_at, _utc_now(), idem, self._sequence, raw_result, None if verified else 'verification_failed', verified)
            except TimeoutError as exc:
                self._sequence += 1
                self._seen_idempotency_keys.add(idem)
                return DeviceActionReceipt(action.action_id, action.action_type, action.capability_name, DeviceActionState.TIMEOUT_PENDING_VERIFY, started_at, _utc_now(), idem, self._sequence, {'device_connection_state': 'connected', 'timeout': True}, str(exc) or 'action_timeout_pending_verify', False)
            finally:
                self._lock_held = False

def make_device_action(action_type: str, capability_name: str, arguments: Optional[Dict[str, Any]] = None, *, idempotency_key: Optional[str] = None, timeout_seconds: int = 60, depends_on: Optional[Sequence[str]] = None) -> DeviceAction:
    return DeviceAction(action_type=action_type, capability_name=capability_name, arguments=arguments or {}, idempotency_key=idempotency_key, timeout_profile=TimeoutProfile(seconds=timeout_seconds), depends_on=depends_on or [])
