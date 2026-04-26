#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from infrastructure.production_gate import run_production_gate
root=Path(__file__).resolve().parents[1]
out=root/'V13_0_PRODUCTION_GATE_REPORT.json'
r=run_production_gate(root=root,output_path=out,soak_iterations=10)
assert r['production_gate']=='pass',r
print(json.dumps({'ok':True,'version':'V13.0','production_gate':r['production_gate'],'report':str(out),'checks':r['checks']},ensure_ascii=False,indent=2))
os._exit(0)
