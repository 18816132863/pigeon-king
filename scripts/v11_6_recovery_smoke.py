#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_adapter.runtime_state_store import register_action, transition_action, connect, get_action
from platform_adapter.recovery_manager import recover_stale_actions, recovery_status

td = tempfile.mkdtemp(prefix='pk_v116_')
db = Path(td) / 'runtime.db'
a = register_action(capability='search', op_name='lookup', payload={'q':'stale'}, db_path=db)
transition_action(a.action_id, 'running', reason='simulate_crash', db_path=db)
with connect(db) as conn:
    conn.execute('UPDATE runtime_actions SET updated_at_ms=1 WHERE action_id=?', (a.action_id,))
report = recover_stale_actions(stale_after_ms=1000, db_path=db).to_dict()
current = get_action(a.action_id, db_path=db).to_dict()
assert report['recovered'] >= 1, report
assert current['state'] == 'queued', current
print(json.dumps({'ok': True, 'version':'V11.6', 'report':report, 'status':recovery_status(db)}, ensure_ascii=False, indent=2))
