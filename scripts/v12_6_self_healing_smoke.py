#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_adapter.runtime_state_store import register_action, transition_action, enqueue_action, connect, _now_ms, get_action
from platform_adapter.self_healing_supervisor import run_self_healing, self_healing_status
root=Path(__file__).resolve().parents[1]
db=Path(tempfile.mkdtemp(prefix='pk_v126_'))/'runtime.db'
a=register_action(capability='local_runtime',op_name='stale_running_probe',payload={'x':1},task_id='v126',risk_level='L2',db_path=db)
transition_action(a.action_id,'running',reason='seed_stale',db_path=db)
q=register_action(capability='local_runtime',op_name='expired_lease_probe',payload={'x':2},task_id='v126q',risk_level='L1',db_path=db)
enqueue_action(q.action_id,delivery_mode='probe',db_path=db)
with connect(db) as conn:
    conn.execute('UPDATE runtime_actions SET updated_at_ms=? WHERE action_id=?',(_now_ms()-600000,a.action_id))
    conn.execute("UPDATE runtime_delivery_queue SET state='leased', not_before_ms=?, updated_at_ms=? WHERE action_id=?",(_now_ms()-1,_now_ms()-600000,q.action_id))
r=run_self_healing(db_path=db,stale_after_ms=1000)
assert r['gate']=='pass',r
assert r['recovery']['recovered']>=1,r
assert len(r['lease_repairs'])>=1,r
assert get_action(a.action_id,db_path=db).state=='queued'
print(json.dumps({'ok':True,'version':'V12.6','gate':r['gate'],'status':self_healing_status(db)},ensure_ascii=False,indent=2))
os._exit(0)
