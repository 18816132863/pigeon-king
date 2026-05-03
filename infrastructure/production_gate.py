"""V13.0 Production Gate: one-shot local production readiness report."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from infrastructure.platform_adapter.runtime_state_store import register_action, transition_action, enqueue_action
from infrastructure.platform_adapter.self_healing_supervisor import run_self_healing
from governance.audit.execution_audit_ledger import audit_event, build_audit_report
from governance.policy.risk_tier_matrix import evaluate_action_risk, risk_matrix_report
from infrastructure.long_run_soak import run_long_run_soak
from infrastructure.upgrade_orchestrator import run_upgrade_gate
from infrastructure.release_manifest import build_release_manifest
from infrastructure.slo_monitor import build_slo_report


def run_production_gate(
    *,
    root: str | Path = '.',
    db_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    soak_iterations: int = 12,
) -> Dict[str, Any]:
    root = Path(root).resolve()
    db = Path(db_path) if db_path else Path(tempfile.mkdtemp(prefix='pk_v130_')) / 'runtime.db'

    # Seed one stale running action and one expired lease to verify healing is active.
    stale = register_action(capability='local_runtime', op_name='production_gate_stale_probe', payload={'probe': 'stale'}, task_id='v13-stale', risk_level='L2', db_path=db)
    transition_action(stale.action_id, 'running', reason='seed_stale_for_v13_gate', db_path=db)
    from infrastructure.platform_adapter.runtime_state_store import connect, _now_ms
    from contextlib import closing
    with closing(connect(db)) as conn:
        conn.execute('UPDATE runtime_actions SET updated_at_ms=? WHERE action_id=?', (_now_ms() - 600_000, stale.action_id))

    queued = register_action(capability='local_runtime', op_name='production_gate_queue_probe', payload={'probe': 'lease'}, task_id='v13-lease', risk_level='L1', db_path=db)
    enqueue_action(queued.action_id, delivery_mode='v13_gate', db_path=db)
    with closing(connect(db)) as conn:
        conn.execute("UPDATE runtime_delivery_queue SET state='leased', not_before_ms=?, updated_at_ms=? WHERE action_id=?", (_now_ms() - 1, _now_ms() - 600_000, queued.action_id))

    healing = run_self_healing(db_path=db, stale_after_ms=1_000, max_blocked_actions=10)
    audit_event(action_id=stale.action_id, actor='production_gate', event_type='gate_probe', decision='healed', risk_level='L2', reason='production_gate_seed_verified', details={'healing_gate': healing.get('gate')}, db_path=db)
    risk_decision = evaluate_action_risk(capability='local_runtime', op_name='send_side_effect', payload={'side_effecting': True, 'recipient': 'local'}, connected=True, confirmed=False, db_path=db)
    audit = build_audit_report(db_path=db, limit=500)
    risk = risk_matrix_report(db_path=db)
    slo = build_slo_report(db_path=db, max_blocked_actions=10, max_leased_items=0)
    soak = run_long_run_soak(iterations=soak_iterations)
    upgrade = run_upgrade_gate(root=root)
    manifest = build_release_manifest(root=root, db_path=db)

    blocking = []
    checks = {
        'self_healing': healing.get('gate'),
        'audit': audit.get('gate'),
        'risk_matrix': risk.get('gate'),
        'slo': slo.get('gate'),
        'long_run_soak': soak.get('gate'),
        'upgrade_gate': upgrade.get('upgrade_gate'),
        'release_manifest': manifest.get('release_gate'),
    }
    for name, gate in checks.items():
        if gate not in ('pass', 'warn'):
            blocking.append(f'{name}_failed')
    if risk_decision.get('decision') != 'requires_confirmation':
        blocking.append('high_risk_confirmation_rule_failed')
    if audit.get('entry_count', 0) <= 0:
        blocking.append('audit_empty')

    report = {
        'version': 'V13.0',
        'production_gate': 'pass' if not blocking else 'fail',
        'blocking_items': blocking,
        'db_path': str(db),
        'checks': checks,
        'details': {
            'self_healing': {'recovered': healing.get('recovery', {}).get('recovered'), 'lease_repairs': len(healing.get('lease_repairs', []))},
            'audit': {'entry_count': audit.get('entry_count'), 'by_decision': audit.get('by_decision')},
            'risk_matrix': {'by_risk': risk.get('by_risk'), 'by_decision': risk.get('by_decision'), 'high_risk_probe': risk_decision},
            'slo': {'findings': slo.get('findings'), 'metrics': slo.get('metrics')},
            'long_run_soak': {'iterations': soak.get('iterations'), 'completed': soak.get('completed'), 'blocking_items': soak.get('blocking_items')},
            'upgrade_gate': {'blocking_items': upgrade.get('blocking_items')},
            'release_manifest': {'version': manifest.get('version'), 'blocking_items': manifest.get('blocking_items'), 'file_count': manifest.get('file_manifest', {}).get('file_count')},
        },
    }
    if output_path:
        Path(output_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report
