#!/usr/bin/env python3
"""Gate for V24.7 global end-side serial execution."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def main() -> int:
    smoke = ROOT/'scripts'/'v24_7_end_side_global_serial_smoke.py'
    result = subprocess.run([sys.executable, str(smoke)], cwd=str(ROOT), text=True, capture_output=True, timeout=120)
    report = {'v24_7_end_side_global_serial_gate': 'pass' if result.returncode == 0 else 'fail', 'smoke_returncode': result.returncode, 'stdout_tail': result.stdout[-4000:], 'stderr_tail': result.stderr[-4000:]}
    (ROOT/'V24_7_END_SIDE_GLOBAL_SERIAL_GATE.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return result.returncode
if __name__ == '__main__':
    raise SystemExit(main())
