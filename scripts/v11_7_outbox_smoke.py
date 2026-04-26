#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_adapter.runtime_state_store import register_action, enqueue_action, get_action
from platform_adapter.delivery_outbox import lease_next, mark_delivered, mark_failed, outbox_summary

td = tempfile.mkdtemp(prefix='pk_v117_')
db = Path(td) / 'runtime.db'
a = register_action(capability='file_write', op_name='write', payload={'path':'x.txt'}, db_path=db)
qid = enqueue_action(a.action_id, delivery_mode='local_fallback', db_path=db)
leased = lease_next(limit=1, db_path=db)
assert leased and leased[0]['queue_id'] == qid, leased
delivered = mark_delivered(qid, result={'ok': True, 'receipt':'local:x'}, db_path=db)
assert get_action(a.action_id, db_path=db).state == 'completed'
b = register_action(capability='MESSAGE_SENDING', op_name='send', payload={'body':'timeout'}, db_path=db)
q2 = enqueue_action(b.action_id, delivery_mode='confirm_then_queue', db_path=db)
lease_next(limit=1, db_path=db)
failed = mark_failed(q2, error='timeout', side_effecting=True, result_uncertain=True, db_path=db)
assert failed['status'] == 'blocked', failed
print(json.dumps({'ok': True, 'version':'V11.7', 'delivered':delivered, 'failed':failed, 'summary':outbox_summary(db)}, ensure_ascii=False, indent=2))
