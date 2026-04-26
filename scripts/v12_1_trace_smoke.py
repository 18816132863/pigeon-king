#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_adapter.runtime_state_store import register_action
from platform_adapter.trace_recorder import record_trace, build_trace_report

db=Path(tempfile.mkdtemp(prefix='pk_v121_'))/'runtime.db'; a=register_action(capability='device.notification',op_name='send',payload={'title':'trace'},db_path=db)
record_trace(stage='plan',status='ok',action_id=a.action_id,correlation_id='trace-smoke',db_path=db); record_trace(stage='execute',status='ok',payload={'result':'local'},action_id=a.action_id,correlation_id='trace-smoke',db_path=db)
r=build_trace_report(correlation_id='trace-smoke',db_path=db); assert r['trace_count']==2,r; print(json.dumps({'ok':True,'version':'V12.1','trace_count':r['trace_count']},ensure_ascii=False,indent=2))

os._exit(0)
