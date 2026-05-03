"""V12.6 Self Healing Supervisor: local-only repair loop for runtime actions and outbox leases.

This module does not call cloud services or external adapters. It performs deterministic
SQLite-based recovery so the runtime can heal stale local state before an operator has to
intervene.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from infrastructure.platform_adapter.runtime_state_store import connect, init_runtime_tables, _now_ms, _json
from infrastructure.platform_adapter.recovery_manager import recover_stale_actions, init_recovery_tables
from infrastructure.platform_adapter.delivery_outbox import init_outbox_tables
from infrastructure.slo_monitor import build_slo_report


@dataclass
class LeaseRepair:
    queue_id: int
    action_id: str
    from_state: str
    to_state: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def init_self_healing_tables(db_path: Optional[Path] = None) -> None:
    init_recovery_tables(db_path)
    init_outbox_tables(db_path)
    with closing(connect(db_path)) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runtime_self_healing_runs(
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT NOT NULL,
                gate TEXT NOT NULL,
                repaired_actions INTEGER DEFAULT 0,
                repaired_leases INTEGER DEFAULT 0,
                report_json TEXT,
                created_at_ms INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runtime_self_healing_events(
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                ref_id TEXT,
                event_json TEXT,
                created_at_ms INTEGER NOT NULL
            );
            """
        )


def requeue_expired_leases(*, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Move expired leased outbox rows back to pending so delivery can resume safely."""
    init_self_healing_tables(db_path)
    now = _now_ms()
    repairs: List[LeaseRepair] = []
    with closing(connect(db_path)) as conn:
        rows = conn.execute(
            """
            SELECT queue_id, action_id, state, COALESCE(not_before_ms,0) AS not_before_ms
            FROM runtime_delivery_queue
            WHERE state='leased' AND COALESCE(not_before_ms,0) <= ?
            ORDER BY updated_at_ms ASC, queue_id ASC
            """,
            (now,),
        ).fetchall()
        for row in rows:
            conn.execute(
                "UPDATE runtime_delivery_queue SET state='pending', updated_at_ms=?, last_error=NULL WHERE queue_id=?",
                (now, int(row['queue_id'])),
            )
            item = LeaseRepair(int(row['queue_id']), row['action_id'], 'leased', 'pending', 'expired_lease_requeued')
            conn.execute(
                "INSERT INTO runtime_self_healing_events(event_type,ref_id,event_json,created_at_ms) VALUES (?,?,?,?)",
                ('lease_repair', str(item.queue_id), _json(item.to_dict()), now),
            )
            repairs.append(item)
    return [r.to_dict() for r in repairs]


def run_self_healing(
    *,
    db_path: Optional[Path] = None,
    stale_after_ms: int = 120_000,
    mode: str = 'safe',
    max_blocked_actions: int = 10,
) -> Dict[str, Any]:
    """Run one safe local repair pass and return a gateable report."""
    init_self_healing_tables(db_path)
    recovery = recover_stale_actions(stale_after_ms=stale_after_ms, db_path=db_path).to_dict()
    lease_repairs = requeue_expired_leases(db_path=db_path)
    slo = build_slo_report(db_path=db_path, max_blocked_actions=max_blocked_actions)
    blocking: List[str] = []
    if slo.get('gate') == 'fail':
        blocking.append('slo_failed_after_healing')
    gate = 'pass' if not blocking else 'fail'
    report = {
        'version': 'V12.6',
        'mode': mode,
        'gate': gate,
        'blocking_items': blocking,
        'recovery': recovery,
        'lease_repairs': lease_repairs,
        'slo': {'gate': slo.get('gate'), 'findings': slo.get('findings', []), 'metrics': slo.get('metrics', {})},
        'generated_at_ms': _now_ms(),
    }
    with closing(connect(db_path)) as conn:
        cur = conn.execute(
            "INSERT INTO runtime_self_healing_runs(mode,gate,repaired_actions,repaired_leases,report_json,created_at_ms) VALUES (?,?,?,?,?,?)",
            (mode, gate, int(recovery.get('recovered', 0)), len(lease_repairs), _json(report), _now_ms()),
        )
        report['run_id'] = int(cur.lastrowid)
    return report


def self_healing_status(db_path: Optional[Path] = None) -> Dict[str, Any]:
    init_self_healing_tables(db_path)
    with closing(connect(db_path)) as conn:
        total = conn.execute('SELECT COUNT(*) n FROM runtime_self_healing_runs').fetchone()['n']
        last = conn.execute('SELECT * FROM runtime_self_healing_runs ORDER BY run_id DESC LIMIT 1').fetchone()
    return {
        'version': 'V12.6',
        'runs': int(total or 0),
        'last_gate': last['gate'] if last else None,
        'last_run_id': int(last['run_id']) if last else None,
        'generated_at_ms': _now_ms(),
    }
