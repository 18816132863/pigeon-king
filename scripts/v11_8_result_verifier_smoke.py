#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_adapter.runtime_state_store import register_action, get_action
from platform_adapter.result_verifier import build_result_contract, verify_action_result

td = tempfile.mkdtemp(prefix='pk_v118_')
db = Path(td) / 'runtime.db'
a = register_action(capability='file_write', op_name='write', payload={'path':'ok.txt'}, db_path=db)
contract = build_result_contract(capability='file_write', op_name='write', side_effecting=True)
ok = verify_action_result(a.action_id, result={'ok': True, 'status':'done', 'receipt':'local:ok'}, required_fields=contract['required_fields'], db_path=db)
assert ok['verified'] is True and get_action(a.action_id, db_path=db).state == 'completed', ok
b = register_action(capability='MESSAGE_SENDING', op_name='send', payload={'body':'maybe'}, db_path=db)
hold = verify_action_result(b.action_id, result={'ok': True, 'status':'timeout'}, required_fields=contract['required_fields'], db_path=db)
assert hold['status'] == 'hold_for_result_check', hold
print(json.dumps({'ok': True, 'version':'V11.8', 'verified':ok, 'held':hold}, ensure_ascii=False, indent=2))
