#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=["scripts/v11_1_state_store_smoke.py","scripts/v11_2_timeout_circuit_smoke.py","scripts/v11_3_capability_registry_smoke.py","scripts/v11_4_autopilot_smoke.py","scripts/v11_5_release_gate.py"]
def main():
    for script in SCRIPTS:
        print(f"\n=== {script} ===")
        subprocess.run([sys.executable,str(ROOT/script)],check=True,cwd=str(ROOT))
    print("\nV11.1-V11.5 smoke checks passed.")
if __name__=="__main__": main()
