#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_adapter.runtime_state_store import register_action, transition_action
from infrastructure.slo_monitor import build_slo_report

db=Path(tempfile.mkdtemp(prefix='pk_v124_'))/'runtime.db'; a=register_action(capability='device.note',op_name='write',payload={'note':'slo'},db_path=db); transition_action(a.action_id,'completed',reason='slo_smoke_done',db_path=db); r=build_slo_report(db_path=db); assert r['gate']=='pass',r; print(json.dumps({'ok':True,'version':'V12.4','gate':r['gate'],'metrics':r['metrics']},ensure_ascii=False,indent=2))

os._exit(0)
