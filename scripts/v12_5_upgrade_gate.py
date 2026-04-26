#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from infrastructure.upgrade_orchestrator import run_upgrade_gate
root=Path(__file__).resolve().parents[1]; out=root/'V12_5_UPGRADE_REPORT.json'; r=run_upgrade_gate(root=root,db_path=Path(tempfile.mkdtemp(prefix='pk_v125_'))/'runtime.db',output_path=out); assert r['upgrade_gate']=='pass',r['blocking_items']; print(json.dumps({'ok':True,'version':'V12.5','upgrade_gate':r['upgrade_gate'],'report':str(out)},ensure_ascii=False,indent=2))

os._exit(0)
