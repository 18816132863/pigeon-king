#!/usr/bin/env python3
from __future__ import annotations
import subprocess, sys, os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
scripts=[
    'scripts/v12_6_self_healing_smoke.py',
    'scripts/v12_7_audit_ledger_smoke.py',
    'scripts/v12_8_risk_matrix_smoke.py',
    'scripts/v12_9_long_run_soak_smoke.py',
    'scripts/v13_0_production_gate.py',
]
for s in scripts:
    print(f'\n===== RUN {s} =====', flush=True)
    subprocess.run([sys.executable,str(root/s)],cwd=str(root),check=True)
print('\nV12.6 -> V13.0 all smoke checks passed.', flush=True)
os._exit(0)
