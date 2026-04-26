#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_adapter.replay_harness import run_default_replay
r=run_default_replay(db_path=Path(tempfile.mkdtemp(prefix='pk_v122_'))/'runtime.db'); assert r['gate']=='pass',r; assert r['final_action']['state']=='completed',r['final_action']; print(json.dumps({'ok':True,'version':'V12.2','gate':r['gate'],'final_state':r['final_action']['state']},ensure_ascii=False,indent=2))

os._exit(0)
