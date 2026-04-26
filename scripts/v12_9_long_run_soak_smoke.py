#!/usr/bin/env python3
from __future__ import annotations
import json, sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from infrastructure.long_run_soak import run_long_run_soak
r=run_long_run_soak(iterations=15)
assert r['gate']=='pass',r
print(json.dumps({'ok':True,'version':'V12.9','gate':r['gate'],'completed':r['completed'],'duplicates_detected':r['duplicates_detected']},ensure_ascii=False,indent=2))
os._exit(0)
