"""V12.9 Long Run Soak: deterministic local soak scenarios for repeated executions."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from platform_adapter.runtime_state_store import register_action, enqueue_action, summarize_runtime, get_action
from platform_adapter.delivery_outbox import lease_next, mark_delivered, outbox_summary
from platform_adapter.result_verifier import verify_action_result
from platform_adapter.trace_recorder import record_trace, build_trace_report
from governance.policy.risk_tier_matrix import evaluate_action_risk, risk_matrix_report
from governance.audit.execution_audit_ledger import build_audit_report
from infrastructure.slo_monitor import build_slo_report


def run_long_run_soak(
    *,
    iterations: int = 30,
    db_path: Optional[Path] = None,
    correlation_id: str = 'v12_9_soak',
) -> Dict[str, Any]:
    db = Path(db_path) if db_path else Path(tempfile.mkdtemp(prefix='pk_v129_')) / 'runtime.db'
    completed = 0
    duplicates_detected = 0
    for i in range(max(1, iterations)):
        payload = {'i': i, 'side_effecting': False, 'content': f'local-soak-{i}'}
        action = register_action(capability='local_runtime', op_name='create_traceable_task', payload=payload, task_id=f'soak-{i}', risk_level='L2', db_path=db)
        record_trace(stage='register', status='ok', action_id=action.action_id, correlation_id=correlation_id, payload={'i': i}, db_path=db)
        evaluate_action_risk(action_id=action.action_id, connected=True, confirmed=True, db_path=db)
        enqueue_action(action.action_id, delivery_mode='local_soak', db_path=db)
        leased = lease_next(limit=1, lease_ms=5_000, db_path=db)
        if not leased:
            record_trace(stage='lease', status='empty', action_id=action.action_id, correlation_id=correlation_id, db_path=db)
            continue
        mark_delivered(leased[0]['queue_id'], result={'ok': True, 'status': 'delivered', 'receipt': f'soak-{i}'}, db_path=db)
        verify_action_result(action.action_id, result={'ok': True, 'status': 'delivered', 'receipt': f'soak-{i}'}, required_fields=['ok', 'status', 'receipt'], db_path=db)
        completed += 1
        record_trace(stage='complete', status='ok', action_id=action.action_id, correlation_id=correlation_id, payload={'i': i}, db_path=db)

    # Explicit idempotency probe: same task/payload twice must not create another live action.
    dup_payload = {'stable': True}
    a1 = register_action(capability='local_runtime', op_name='idempotency_probe', payload=dup_payload, task_id='soak-dup', risk_level='L1', db_path=db)
    a2 = register_action(capability='local_runtime', op_name='idempotency_probe', payload=dup_payload, task_id='soak-dup', risk_level='L1', db_path=db)
    if getattr(a2, 'duplicated', False) or a1.action_id == a2.action_id:
        duplicates_detected += 1

    slo = build_slo_report(db_path=db, max_blocked_actions=0, max_leased_items=0)
    runtime = summarize_runtime(db)
    outbox = outbox_summary(db)
    traces = build_trace_report(correlation_id=correlation_id, db_path=db)
    audit = build_audit_report(db_path=db, limit=500)
    risk = risk_matrix_report(db_path=db)
    blocking = []
    if completed != max(1, iterations):
        blocking.append('not_all_soak_iterations_completed')
    if duplicates_detected < 1:
        blocking.append('idempotency_probe_failed')
    if slo.get('gate') == 'fail':
        blocking.append('slo_failed')
    report = {
        'version': 'V12.9',
        'gate': 'pass' if not blocking else 'fail',
        'blocking_items': blocking,
        'db_path': str(db),
        'iterations': max(1, iterations),
        'completed': completed,
        'duplicates_detected': duplicates_detected,
        'runtime': runtime,
        'outbox': outbox,
        'slo': {'gate': slo.get('gate'), 'findings': slo.get('findings', []), 'metrics': slo.get('metrics', {})},
        'trace_count': traces.get('trace_count'),
        'audit_entries': audit.get('entry_count'),
        'risk_summary': {'by_risk': risk.get('by_risk'), 'by_decision': risk.get('by_decision')},
    }
    return report
