#!/usr/bin/env python3
from pathlib import Path
import json, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from infrastructure.ops_health import write_health_report
def main():
    out=Path("V11_5_HEALTH_REPORT.json")
    report=write_health_report(out)
    print(json.dumps({"ok":True,"report":str(out),"release_gate":report["release_gate"],"warnings":report["blocking_or_warning_items"]},ensure_ascii=False,indent=2))
if __name__=="__main__":
    main(); os._exit(0)
