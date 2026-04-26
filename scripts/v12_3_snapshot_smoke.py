#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_adapter.runtime_state_store import register_action, transition_action, get_action
from platform_adapter.snapshot_manager import create_snapshot, restore_snapshot

td=Path(tempfile.mkdtemp(prefix='pk_v123_')); db=td/'runtime.db'; a=register_action(capability='device.calendar',op_name='create',payload={'title':'snap'},db_path=db); s=create_snapshot(db_path=db,snapshot_dir=td/'snapshots',label='before_transition'); transition_action(a.action_id,'completed',reason='after_snapshot',db_path=db); restored=td/'restored.db'; rr=restore_snapshot(snapshot_path=Path(s['snapshot_path']),target_db_path=restored,expected_sha256=s['sha256']); ra=get_action(a.action_id,db_path=restored); assert rr['restored'] is True,rr; assert ra.state=='planned',ra.to_dict(); print(json.dumps({'ok':True,'version':'V12.3','restored_state':ra.state},ensure_ascii=False,indent=2))

os._exit(0)
