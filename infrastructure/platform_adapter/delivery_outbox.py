"""V11.7 Delivery Outbox: safe local queue leasing and idempotent delivery bookkeeping."""
from __future__ import annotations

import json
from contextlib import closing
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from infrastructure.platform_adapter.runtime_state_store import connect, init_runtime_tables, get_action, transition_action, _now_ms, _json
from infrastructure.platform_adapter.timeout_circuit import TimeoutBudget, CircuitBreaker


@dataclass
class OutboxItem:
    queue_id: int
    action_id: str
    delivery_mode: str
    state: str
    attempts: int
    payload: Dict[str, Any]
    idempotency_key: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def init_outbox_tables(db_path: Optional[Path] = None) -> None:
    init_runtime_tables(db_path)
    with closing(connect(db_path)) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runtime_outbox_receipts (
                receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                queue_id INTEGER NOT NULL,
                action_id TEXT NOT NULL,
                idempotency_key TEXT NOT NULL,
                status TEXT NOT NULL,
                receipt_json TEXT,
                created_at_ms INTEGER NOT NULL
            );
            """
        )


def lease_next(*, limit: int = 10, lease_ms: int = 60_000, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    init_outbox_tables(db_path)
    now = _now_ms()
    leased: List[OutboxItem] = []
    with closing(connect(db_path)) as conn:
        rows = conn.execute(
            """
            SELECT q.queue_id,q.action_id,q.delivery_mode,q.state,q.attempts,a.payload_json,a.idempotency_key
            FROM runtime_delivery_queue q
            JOIN runtime_actions a ON a.action_id=q.action_id
            WHERE q.state='pending' AND COALESCE(q.not_before_ms,0)<=?
            ORDER BY q.created_at_ms ASC
            LIMIT ?
            """,
            (now, max(1, limit)),
        ).fetchall()
        for r in rows:
            conn.execute(
                "UPDATE runtime_delivery_queue SET state='leased', attempts=attempts+1, not_before_ms=?, updated_at_ms=? WHERE queue_id=? AND state='pending'",
                (now + max(lease_ms, 1_000), now, r["queue_id"]),
            )
            try:
                payload = json.loads(r["payload_json"] or "{}")
            except Exception:
                payload = {"raw": r["payload_json"]}
            leased.append(OutboxItem(int(r["queue_id"]), r["action_id"], r["delivery_mode"], "leased", int(r["attempts"] or 0) + 1, payload, r["idempotency_key"]))
    for item in leased:
        transition_action(item.action_id, "running", reason="outbox_lease_acquired", db_path=db_path)
    return [i.to_dict() for i in leased]


def mark_delivered(queue_id: int, *, result: Optional[Dict[str, Any]] = None, db_path: Optional[Path] = None) -> Dict[str, Any]:
    init_outbox_tables(db_path)
    now = _now_ms()
    result = result or {"delivered": True}
    with closing(connect(db_path)) as conn:
        row = conn.execute("SELECT * FROM runtime_delivery_queue WHERE queue_id=?", (queue_id,)).fetchone()
        if not row:
            raise KeyError(f"unknown queue_id: {queue_id}")
        action = get_action(row["action_id"], db_path=db_path)
        conn.execute("UPDATE runtime_delivery_queue SET state='delivered', updated_at_ms=? WHERE queue_id=?", (now, queue_id))
        conn.execute(
            "INSERT INTO runtime_outbox_receipts(queue_id,action_id,idempotency_key,status,receipt_json,created_at_ms) VALUES (?,?,?,?,?,?)",
            (queue_id, row["action_id"], action.idempotency_key if action else "unknown", "delivered", _json(result), now),
        )
        action_id = row["action_id"]
    transition_action(action_id, "completed", reason="outbox_mark_delivered", result=result, db_path=db_path)
    return {"queue_id": queue_id, "status": "delivered", "action_id": action_id}


def mark_failed(queue_id: int, *, error: str, side_effecting: bool = True, result_uncertain: bool = True, db_path: Optional[Path] = None) -> Dict[str, Any]:
    init_outbox_tables(db_path)
    now = _now_ms()
    with closing(connect(db_path)) as conn:
        row = conn.execute("SELECT * FROM runtime_delivery_queue WHERE queue_id=?", (queue_id,)).fetchone()
        if not row:
            raise KeyError(f"unknown queue_id: {queue_id}")
        attempts = int(row["attempts"] or 0)
        action = get_action(row["action_id"], db_path=db_path)
        decision = TimeoutBudget(max_attempts=3).decide_retry(
            attempt=attempts,
            side_effecting=side_effecting,
            result_uncertain=result_uncertain,
            last_status="timeout" if result_uncertain else "failed",
        )
        next_state = "pending" if decision.allowed else "blocked"
        not_before_ms = now + int(decision.retry_after_ms or 0)
        conn.execute(
            "UPDATE runtime_delivery_queue SET state=?, not_before_ms=?, last_error=?, updated_at_ms=? WHERE queue_id=?",
            (next_state, not_before_ms, error, now, queue_id),
        )
        conn.execute(
            "INSERT INTO runtime_outbox_receipts(queue_id,action_id,idempotency_key,status,receipt_json,created_at_ms) VALUES (?,?,?,?,?,?)",
            (queue_id, row["action_id"], action.idempotency_key if action else "unknown", next_state, _json(decision.to_dict()), now),
        )
        action_id = row["action_id"]

    if next_state == "blocked":
        transition_action(action_id, "hold_for_result_check", reason=decision.reason, error=error, db_path=db_path)
    else:
        transition_action(action_id, "queued", reason=decision.reason, error=error, db_path=db_path)
    CircuitBreaker(action_id, db_path=db_path).record_failure(error)
    return {"queue_id": queue_id, "status": next_state, "decision": decision.to_dict()}


def outbox_summary(db_path: Optional[Path] = None) -> Dict[str, Any]:
    init_outbox_tables(db_path)
    with closing(connect(db_path)) as conn:
        q = {r["state"]: int(r["n"]) for r in conn.execute("SELECT state,COUNT(*) n FROM runtime_delivery_queue GROUP BY state").fetchall()}
        receipts = {r["status"]: int(r["n"]) for r in conn.execute("SELECT status,COUNT(*) n FROM runtime_outbox_receipts GROUP BY status").fetchall()}
    return {"queue": q, "receipts": receipts, "generated_at_ms": _now_ms()}
