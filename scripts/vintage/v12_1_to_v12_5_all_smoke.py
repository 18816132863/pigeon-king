#!/usr/bin/env python3
from __future__ import annotations
import subprocess, sys, os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for s in ['scripts/v12_1_trace_smoke.py','scripts/v12_2_replay_smoke.py','scripts/v12_3_snapshot_smoke.py','scripts/v12_4_slo_smoke.py','scripts/v12_5_upgrade_gate.py']:
    print(f'\n===== RUN {s} ====='); subprocess.run([sys.executable,str(root/s)],cwd=str(root),check=True)
print('\nV12.1 -> V12.5 all smoke checks passed.')

os._exit(0)
