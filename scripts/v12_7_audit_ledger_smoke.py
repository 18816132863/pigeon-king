#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_adapter.runtime_state_store import register_action, transition_action
from governance.audit.execution_audit_ledger import audit_event, build_audit_report
db=Path(tempfile.mkdtemp(prefix='pk_v127_'))/'runtime.db'
a=register_action(capability='local_runtime',op_name='audit_probe',payload={'audit':True},task_id='v127',risk_level='L2',db_path=db)
audit_event(action_id=a.action_id,actor='smoke',event_type='decision',decision='allow_with_trace',before_state='planned',after_state='running',reason='audit smoke',db_path=db)
transition_action(a.action_id,'running',reason='audit_transition',db_path=db)
report=build_audit_report(db_path=db,action_id=a.action_id)
assert report['gate']=='pass' and report['entry_count']>=1,report
print(json.dumps({'ok':True,'version':'V12.7','entry_count':report['entry_count'],'by_decision':report['by_decision']},ensure_ascii=False,indent=2))
os._exit(0)
