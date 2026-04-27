"""
V23.7 Action Idempotency Guard.

Layer: L4 Execution.

Purpose:
- Side-effect actions must not be duplicated during retry, resume, or receipt timeout.
- The guard stores action fingerprints and their terminal/pending status.
- It is intentionally small and stdlib-only so it can run in device-side environments.

This module does NOT call tools directly.  It only protects execution/outbox.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import hashlib
import json
import time


ARCHITECTURE_LAYER = "L4 Execution"
TERMINAL_STATUSES = {"success", "success_with_timeout_receipt", "failed", "cancelled"}


def stable_action_key(action_type: str, payload: dict[str, Any]) -> str:
    """Create a deterministic key for an action and payload."""
    normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(f"{action_type}:{normalized}".encode("utf-8")).hexdigest()[:24]
    return f"{action_type}:{digest}"


@dataclass
class ActionRecord:
    action_key: str
    action_type: str
    status: str
    payload: dict[str, Any]
    created_at: float
    updated_at: float
    receipt: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IdempotencyGuard:
    def __init__(self, store_path: str | Path):
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_path.exists():
            self.store_path.write_text("{}", encoding="utf-8")

    def _load(self) -> dict[str, dict[str, Any]]:
        try:
            raw = self.store_path.read_text(encoding="utf-8").strip() or "{}"
            data = json.loads(raw)
            if not isinstance(data, dict):
                return {}
            return data
        except Exception:
            return {}

    def _save(self, data: dict[str, dict[str, Any]]) -> None:
        tmp = self.store_path.with_suffix(self.store_path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.store_path)

    def reserve(self, action_type: str, payload: dict[str, Any]) -> ActionRecord:
        key = stable_action_key(action_type, payload)
        data = self._load()
        existing = data.get(key)
        now = time.time()
        if existing:
            return ActionRecord(**existing)
        rec = ActionRecord(
            action_key=key,
            action_type=action_type,
            status="reserved",
            payload=payload,
            created_at=now,
            updated_at=now,
        )
        data[key] = rec.to_dict()
        self._save(data)
        return rec

    def should_execute(self, record: ActionRecord) -> bool:
        """Return False for successful or in-flight actions to avoid duplicate side effects."""
        return record.status not in TERMINAL_STATUSES and record.status not in {"running", "pending_verify"}

    def mark(self, action_key: str, status: str, receipt: dict[str, Any] | None = None) -> ActionRecord:
        data = self._load()
        if action_key not in data:
            raise KeyError(f"unknown action_key: {action_key}")
        item = data[action_key]
        item["status"] = status
        item["updated_at"] = time.time()
        if receipt is not None:
            item["receipt"] = receipt
        data[action_key] = item
        self._save(data)
        return ActionRecord(**item)

    def find_duplicate(self, action_type: str, payload: dict[str, Any]) -> ActionRecord | None:
        key = stable_action_key(action_type, payload)
        data = self._load()
        if key not in data:
            return None
        return ActionRecord(**data[key])
