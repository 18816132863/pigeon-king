"""V12.7 Execution Audit Ledger: who/what/why audit trail for local runtime decisions."""
from __future__ import annotations

import json
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from platform_adapter.runtime_state_store import connect, init_runtime_tables, get_action, _now_ms, _json


@dataclass
class AuditEntry:
    audit_id: int
    action_id: Optional[str]
    actor: str
    event_type: str
    decision: str
    risk_level: str
    before_state: Optional[str]
    after_state: Optional[str]
    reason: str
    details: Dict[str, Any]
    created_at_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def init_audit_tables(db_path: Optional[Path] = None) -> None:
    init_runtime_tables(db_path)
    with closing(connect(db_path)) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runtime_execution_audit(
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_id TEXT,
                actor TEXT NOT NULL,
                event_type TEXT NOT NULL,
                decision TEXT NOT NULL,
                risk_level TEXT DEFAULT 'L1',
                before_state TEXT,
                after_state TEXT,
                reason TEXT,
                details_json TEXT,
                created_at_ms INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_execution_audit_action ON runtime_execution_audit(action_id, created_at_ms);
            CREATE INDEX IF NOT EXISTS idx_execution_audit_type ON runtime_execution_audit(event_type, created_at_ms);
            """
        )


def _load(value: Optional[str]) -> Dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {'value': parsed}
    except Exception:
        return {'raw': value}


def audit_event(
    *,
    action_id: Optional[str] = None,
    actor: str = 'runtime',
    event_type: str = 'decision',
    decision: str = 'recorded',
    risk_level: Optional[str] = None,
    before_state: Optional[str] = None,
    after_state: Optional[str] = None,
    reason: str = '',
    details: Optional[Dict[str, Any]] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    init_audit_tables(db_path)
    action = get_action(action_id, db_path=db_path) if action_id else None
    risk = risk_level or (action.risk_level if action else 'L1')
    now = _now_ms()
    with closing(connect(db_path)) as conn:
        cur = conn.execute(
            """
            INSERT INTO runtime_execution_audit(action_id,actor,event_type,decision,risk_level,before_state,after_state,reason,details_json,created_at_ms)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (action_id, actor, event_type, decision, risk, before_state, after_state, reason, _json(details or {}), now),
        )
        row = conn.execute('SELECT * FROM runtime_execution_audit WHERE audit_id=?', (cur.lastrowid,)).fetchone()
    return AuditEntry(
        int(row['audit_id']), row['action_id'], row['actor'], row['event_type'], row['decision'], row['risk_level'],
        row['before_state'], row['after_state'], row['reason'] or '', _load(row['details_json']), int(row['created_at_ms'])
    ).to_dict()


def synthesize_from_action_events(*, db_path: Optional[Path] = None, limit: int = 200) -> int:
    """Backfill audit entries from runtime_action_events when explicit audit is missing."""
    init_audit_tables(db_path)
    inserted = 0
    with closing(connect(db_path)) as conn:
        rows = conn.execute(
            """
            SELECT e.action_id,e.from_state,e.to_state,e.reason,e.event_json,e.created_at_ms,a.risk_level
            FROM runtime_action_events e
            LEFT JOIN runtime_actions a ON a.action_id=e.action_id
            ORDER BY e.created_at_ms ASC, e.event_id ASC
            LIMIT ?
            """,
            (max(1, limit),),
        ).fetchall()
        for row in rows:
            exists = conn.execute(
                "SELECT COUNT(*) n FROM runtime_execution_audit WHERE action_id=? AND before_state IS ? AND after_state=? AND created_at_ms=?",
                (row['action_id'], row['from_state'], row['to_state'], int(row['created_at_ms'])),
            ).fetchone()['n']
            if exists:
                continue
            conn.execute(
                """
                INSERT INTO runtime_execution_audit(action_id,actor,event_type,decision,risk_level,before_state,after_state,reason,details_json,created_at_ms)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (row['action_id'], 'runtime_state_store', 'state_transition', 'observed', row['risk_level'] or 'L1', row['from_state'], row['to_state'], row['reason'] or '', row['event_json'] or '{}', int(row['created_at_ms'])),
            )
            inserted += 1
    return inserted


def build_audit_report(*, db_path: Optional[Path] = None, action_id: Optional[str] = None, limit: int = 200) -> Dict[str, Any]:
    init_audit_tables(db_path)
    synthesize_from_action_events(db_path=db_path, limit=limit)
    params: tuple[Any, ...]
    sql: str
    if action_id:
        sql = 'SELECT * FROM runtime_execution_audit WHERE action_id=? ORDER BY created_at_ms ASC, audit_id ASC LIMIT ?'
        params = (action_id, max(1, limit))
    else:
        sql = 'SELECT * FROM runtime_execution_audit ORDER BY created_at_ms DESC, audit_id DESC LIMIT ?'
        params = (max(1, limit),)
    with closing(connect(db_path)) as conn:
        rows = conn.execute(sql, params).fetchall()
    entries = [
        AuditEntry(int(r['audit_id']), r['action_id'], r['actor'], r['event_type'], r['decision'], r['risk_level'], r['before_state'], r['after_state'], r['reason'] or '', _load(r['details_json']), int(r['created_at_ms'])).to_dict()
        for r in rows
    ]
    by_decision: Dict[str, int] = {}
    by_risk: Dict[str, int] = {}
    for e in entries:
        by_decision[e['decision']] = by_decision.get(e['decision'], 0) + 1
        by_risk[e['risk_level']] = by_risk.get(e['risk_level'], 0) + 1
    gate = 'pass' if entries else 'warn'
    return {'version': 'V12.7', 'gate': gate, 'entry_count': len(entries), 'by_decision': by_decision, 'by_risk': by_risk, 'entries': entries, 'generated_at_ms': _now_ms()}
