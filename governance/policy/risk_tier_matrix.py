"""V12.8 Risk Tier Matrix: deterministic local risk classification and enforcement hints."""
from __future__ import annotations

from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from platform_adapter.runtime_state_store import connect, init_runtime_tables, get_action, transition_action, _now_ms, _json
from governance.audit.execution_audit_ledger import audit_event, init_audit_tables

TIER_ORDER = {'L0': 0, 'L1': 1, 'L2': 2, 'L3': 3, 'L4': 4}
DEFAULT_RULES = {
    'read': 'L1', 'search': 'L1', 'probe': 'L1', 'list': 'L1', 'summarize': 'L1',
    'create': 'L2', 'update': 'L2', 'send': 'L3', 'notify': 'L3', 'calendar': 'L3',
    'email': 'L3', 'sms': 'L3', 'payment': 'L4', 'delete': 'L4', 'reset': 'L4', 'external': 'L4',
}


@dataclass
class RiskDecision:
    capability: str
    op_name: str
    risk_level: str
    decision: str
    reason: str
    requires_confirmation: bool
    allow_autopilot: bool
    generated_at_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def init_risk_tables(db_path: Optional[Path] = None) -> None:
    init_runtime_tables(db_path)
    init_audit_tables(db_path)
    with closing(connect(db_path)) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runtime_risk_decisions(
                decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_id TEXT,
                capability TEXT NOT NULL,
                op_name TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                decision TEXT NOT NULL,
                reason TEXT,
                created_at_ms INTEGER NOT NULL
            );
            """
        )


def classify_risk(*, capability: str, op_name: str, payload: Optional[Dict[str, Any]] = None, explicit_risk: Optional[str] = None) -> str:
    if explicit_risk in TIER_ORDER:
        return explicit_risk
    name = f'{capability}.{op_name}'.lower()
    payload = payload or {}
    if payload.get('destructive') is True or payload.get('irreversible') is True:
        return 'L4'
    if payload.get('side_effecting') is True and payload.get('recipient'):
        return 'L3'
    for key, tier in DEFAULT_RULES.items():
        if key in name:
            return tier
    return 'L2'


def decide_for_risk(risk_level: str, *, connected: bool = True, confirmed: bool = False) -> RiskDecision:
    order = TIER_ORDER.get(risk_level, 2)
    if order <= 1:
        decision, reason, requires_confirmation, allow = 'allow', 'low_risk_auto_allowed', False, True
    elif order == 2:
        decision, reason, requires_confirmation, allow = 'allow_with_trace', 'medium_risk_allowed_with_audit', False, True
    elif order == 3:
        if confirmed:
            decision, reason, requires_confirmation, allow = 'allow_after_confirmation', 'high_risk_confirmed', False, True
        else:
            decision, reason, requires_confirmation, allow = 'requires_confirmation', 'high_risk_requires_strong_confirmation', True, False
    else:
        decision, reason, requires_confirmation, allow = 'block_or_manual_review', 'critical_risk_manual_review_required', True, False
    if not connected and decision.startswith('allow'):
        decision, reason, allow = 'queue_local_only', 'not_connected_queue_for_local_delivery', False
    return RiskDecision('', '', risk_level, decision, reason, requires_confirmation, allow, _now_ms())


def evaluate_action_risk(
    *,
    action_id: Optional[str] = None,
    capability: Optional[str] = None,
    op_name: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    connected: bool = True,
    confirmed: bool = False,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    init_risk_tables(db_path)
    action = get_action(action_id, db_path=db_path) if action_id else None
    cap = capability or (action.capability if action else 'unknown')
    op = op_name or (action.op_name if action else 'unknown')
    pay = payload or (action.payload if action else {}) or {}
    risk = classify_risk(capability=cap, op_name=op, payload=pay, explicit_risk=action.risk_level if action else None)
    decision = decide_for_risk(risk, connected=connected, confirmed=confirmed)
    decision.capability = cap
    decision.op_name = op
    d = decision.to_dict()
    with closing(connect(db_path)) as conn:
        conn.execute(
            "INSERT INTO runtime_risk_decisions(action_id,capability,op_name,risk_level,decision,reason,created_at_ms) VALUES (?,?,?,?,?,?,?)",
            (action_id, cap, op, risk, d['decision'], d['reason'], _now_ms()),
        )
    audit_event(action_id=action_id, actor='risk_tier_matrix', event_type='risk_decision', decision=d['decision'], risk_level=risk, reason=d['reason'], details=d, db_path=db_path)
    if action_id and d['decision'] == 'requires_confirmation':
        transition_action(action_id, 'requires_confirmation', reason=d['reason'], db_path=db_path)
    elif action_id and d['decision'] == 'block_or_manual_review':
        transition_action(action_id, 'blocked', reason=d['reason'], error=d['reason'], db_path=db_path)
    return d


def risk_matrix_report(db_path: Optional[Path] = None) -> Dict[str, Any]:
    init_risk_tables(db_path)
    with closing(connect(db_path)) as conn:
        by_risk = {r['risk_level']: int(r['n']) for r in conn.execute('SELECT risk_level,COUNT(*) n FROM runtime_risk_decisions GROUP BY risk_level').fetchall()}
        by_decision = {r['decision']: int(r['n']) for r in conn.execute('SELECT decision,COUNT(*) n FROM runtime_risk_decisions GROUP BY decision').fetchall()}
    return {'version': 'V12.8', 'gate': 'pass', 'by_risk': by_risk, 'by_decision': by_decision, 'generated_at_ms': _now_ms()}
