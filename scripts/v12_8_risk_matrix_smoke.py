#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_adapter.runtime_state_store import register_action, get_action
from governance.policy.risk_tier_matrix import evaluate_action_risk, risk_matrix_report
db=Path(tempfile.mkdtemp(prefix='pk_v128_'))/'runtime.db'
a=register_action(capability='device_sms',op_name='send_message',payload={'side_effecting':True,'recipient':'local'},task_id='v128',risk_level='L3',db_path=db)
d=evaluate_action_risk(action_id=a.action_id,connected=True,confirmed=False,db_path=db)
assert d['risk_level']=='L3' and d['decision']=='requires_confirmation',d
assert get_action(a.action_id,db_path=db).state=='requires_confirmation'
b=register_action(capability='files',op_name='delete_all',payload={'destructive':True},task_id='v128b',risk_level='L4',db_path=db)
d2=evaluate_action_risk(action_id=b.action_id,db_path=db)
assert d2['decision']=='block_or_manual_review',d2
report=risk_matrix_report(db_path=db)
print(json.dumps({'ok':True,'version':'V12.8','report':report},ensure_ascii=False,indent=2))
os._exit(0)
