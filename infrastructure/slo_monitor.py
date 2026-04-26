"""V12.4 local SLO monitor."""
from __future__ import annotations
from contextlib import closing
from pathlib import Path
from typing import Dict, Optional
from platform_adapter.runtime_state_store import connect, summarize_runtime, _now_ms
from platform_adapter.delivery_outbox import init_outbox_tables, outbox_summary

def _scalar(conn, sql, params=()):
    row=conn.execute(sql, params).fetchone(); return int(row[0] or 0) if row else 0

def build_slo_report(*, db_path:Optional[Path]=None, stale_running_ms:int=300000, max_blocked_actions:int=0, max_leased_items:int=10)->Dict:
    init_outbox_tables(db_path); now=_now_ms(); runtime=summarize_runtime(db_path); outbox=outbox_summary(db_path)
    with closing(connect(db_path)) as conn:
        stale=_scalar(conn,"SELECT COUNT(*) FROM runtime_actions WHERE state='running' AND updated_at_ms<?",(now-max(1,stale_running_ms),)); blocked=_scalar(conn,"SELECT COUNT(*) FROM runtime_actions WHERE state IN ('blocked','hold_for_result_check')"); leased=_scalar(conn,"SELECT COUNT(*) FROM runtime_delivery_queue WHERE state='leased'"); pending=_scalar(conn,"SELECT COUNT(*) FROM runtime_delivery_queue WHERE state='pending'")
    findings=[]
    if stale>0: findings.append({'code':'stale_running_actions','severity':'fail','count':stale})
    if blocked>max_blocked_actions: findings.append({'code':'blocked_actions_exceeded','severity':'warn','count':blocked,'limit':max_blocked_actions})
    if leased>max_leased_items: findings.append({'code':'leased_queue_exceeded','severity':'warn','count':leased,'limit':max_leased_items})
    fail=any(f['severity']=='fail' for f in findings); warn=any(f['severity']=='warn' for f in findings)
    return {'version':'V12.4','gate':'fail' if fail else 'warn' if warn else 'pass','findings':findings,'metrics':{'stale_running':stale,'blocked_actions':blocked,'leased_items':leased,'pending_items':pending,'active_count':runtime.get('active_count',0)},'runtime':runtime,'outbox':outbox,'generated_at_ms':now}
