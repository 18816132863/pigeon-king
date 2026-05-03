"""V11.6 Recovery Manager: crash-safe recovery for runtime actions and queues."""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from infrastructure.platform_adapter.runtime_state_store import (
    ACTIVE_STATES,
    connect,
    init_runtime_tables,
    transition_action,
    _now_ms,
    _json,
)
from infrastructure.platform_adapter.timeout_circuit import init_circuit_tables

DEFAULT_STALE_AFTER_MS = 120_000


@dataclass
class RecoveryItem:
    action_id: str
    from_state: str
    to_state: str
    reason: str
    age_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RecoveryReport:
    scanned: int
    recovered: int
    skipped: int
    items: List[Dict[str, Any]]
    generated_at_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def init_recovery_tables(db_path: Optional[Path] = None) -> None:
    init_runtime_tables(db_path)
    init_circuit_tables(db_path)
    with closing(connect(db_path)) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runtime_recovery_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_id TEXT NOT NULL,
                from_state TEXT,
                to_state TEXT NOT NULL,
                reason TEXT,
                event_json TEXT,
                created_at_ms INTEGER NOT NULL
            );
            """
        )


def recover_stale_actions(*, stale_after_ms: int = DEFAULT_STALE_AFTER_MS, db_path: Optional[Path] = None) -> RecoveryReport:
    init_recovery_tables(db_path)
    now = _now_ms()
    threshold = now - max(stale_after_ms, 1_000)
    placeholders = ",".join("?" for _ in ACTIVE_STATES)

    with closing(connect(db_path)) as conn:
        rows = conn.execute(
            f"SELECT action_id,state,updated_at_ms FROM runtime_actions WHERE state IN ({placeholders})",
            tuple(ACTIVE_STATES),
        ).fetchall()

    items: List[RecoveryItem] = []
    skipped = 0
    for row in rows:
        state = row["state"]
        updated_at_ms = int(row["updated_at_ms"] or 0)
        age_ms = now - updated_at_ms
        if updated_at_ms > threshold and state != "running":
            skipped += 1
            continue

        if state == "running":
            to_state, reason = "queued", "stale_running_recovered_to_queue"
        elif state == "planned":
            to_state, reason = "queued", "stale_planned_recovered_to_queue"
        elif state == "queued":
            to_state, reason = "queued", "queued_action_confirmed_recoverable"
        else:
            to_state, reason = "hold_for_result_check", "held_action_preserved_for_probe_check"

        transition_action(row["action_id"], to_state, reason=reason, db_path=db_path)
        item = RecoveryItem(row["action_id"], state, to_state, reason, age_ms)
        with closing(connect(db_path)) as conn:
            conn.execute(
                "INSERT INTO runtime_recovery_events(action_id,from_state,to_state,reason,event_json,created_at_ms) VALUES (?,?,?,?,?,?)",
                (item.action_id, item.from_state, item.to_state, item.reason, _json(item.to_dict()), _now_ms()),
            )
        items.append(item)

    return RecoveryReport(len(rows), len(items), skipped, [i.to_dict() for i in items], now)


def recovery_status(db_path: Optional[Path] = None) -> Dict[str, Any]:
    init_recovery_tables(db_path)
    with closing(connect(db_path)) as conn:
        rows = conn.execute("SELECT to_state,COUNT(*) n FROM runtime_recovery_events GROUP BY to_state").fetchall()
    return {"recovery_events": {r["to_state"]: int(r["n"]) for r in rows}, "generated_at_ms": _now_ms()}
