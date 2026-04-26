#!/usr/bin/env python3
from __future__ import annotations
import subprocess, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
scripts = [
    'scripts/v11_6_recovery_smoke.py',
    'scripts/v11_7_outbox_smoke.py',
    'scripts/v11_8_result_verifier_smoke.py',
    'scripts/v11_9_acceptance_matrix_smoke.py',
    'scripts/v12_0_final_gate.py',
]
for script in scripts:
    print(f'\n===== RUN {script} =====')
    subprocess.run([sys.executable, str(root / script)], cwd=str(root), check=True)
print('\nV11.6 -> V12.0 all smoke checks passed.')
