#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path.cwd()
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

def run_py(code: str):
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT}:{env.get('PYTHONPATH','')}"
    for k in ["OFFLINE_MODE","NO_EXTERNAL_API","DISABLE_LLM_API","DISABLE_THINKING_MODE","NO_REAL_SEND","NO_REAL_PAYMENT","NO_REAL_DEVICE"]:
        env.setdefault(k, "true")
    return subprocess.run([sys.executable, "-S", "-c", code], cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=60)

def write_json(name, payload):
    (REPORTS / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    failures=[]
    checks={}
    # mainline import and run
    proc = run_py("import infrastructure.mainline_hook as mh; r=mh.run(message='这段 JSON 报错了', goal='test'); import json; print(json.dumps(r, ensure_ascii=False))")
    checks["mainline_hook_importable"] = proc.returncode == 0
    if proc.returncode != 0:
        failures.append("mainline_hook_import_or_run_failed")
        checks["mainline_hook_error"] = proc.stderr[-800:]
    else:
        try:
            r=json.loads(proc.stdout.strip().splitlines()[-1])
            checks["mainline_hook_run_ok"] = r.get("status") in ("ok","pass")
            checks["mainline_hook_has_proactive_suggestions"] = "proactive_skill_suggestions" in r
            checks["heavy_chain_not_triggered"] = not r.get("heavy_chain_triggered", False)
            checks["runtime_fusion_summary_ready"] = "runtime_fusion_summary" in r
        except Exception as e:
            failures.append("mainline_hook_output_invalid")
            checks["mainline_hook_parse_error"] = str(e)
    # V98.1 and V104.3 regression actual gates
    for script, key in [("scripts/v98_1_mainline_hook_runtime_gate.py","v98_1_no_regression"),("scripts/v104_3_runtime_fusion_coordination_gate.py","v104_3_no_regression")]:
        p=ROOT/script
        if not p.exists():
            checks[key]=False; failures.append(key+"_script_missing"); continue
        env=os.environ.copy(); env["PYTHONPATH"]=f"{ROOT}:{env.get('PYTHONPATH','')}"
        for k in ["OFFLINE_MODE","NO_EXTERNAL_API","DISABLE_LLM_API","DISABLE_THINKING_MODE","NO_REAL_SEND","NO_REAL_PAYMENT","NO_REAL_DEVICE"]:
            env.setdefault(k,"true")
        pr=subprocess.run([sys.executable,"-S",str(p)], cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=120)
        checks[key]=pr.returncode==0
        if pr.returncode!=0:
            failures.append(key)
            checks[key+"_stderr"]=pr.stderr[-800:]
            checks[key+"_stdout"]=pr.stdout[-800:]
    # proactive skill quality
    proc = run_py("from governance.proactive_skill_matcher import suggest_skills; import json; msgs={'json':'这段 JSON 报错了，帮我格式化和验证字段','excel':'这一堆 Excel 表格数据帮我分析','diagram':'整理系统架构，最好画个流程图'}; print(json.dumps({k:suggest_skills(v, top_k=5) for k,v in msgs.items()}, ensure_ascii=False))")
    quality={}
    if proc.returncode != 0:
        failures.append("proactive_skill_quality_runtime_failed")
        quality["error"]=proc.stderr[-800:]
    else:
        data=json.loads(proc.stdout.strip().splitlines()[-1])
        expected={"json":"json-formatter","excel":"excel-analysis","diagram":"excalidraw"}
        for k, needle in expected.items():
            names=[s.get("name","") for s in data[k].get("suggestions",[])]
            quality[k]={"names":names,"expected":needle,"ok":any(needle in n for n in names[:3 if k!='diagram' else 5])}
            if not quality[k]["ok"]:
                failures.append(f"proactive_quality_{k}")
    checks["proactive_skill_quality"] = quality
    report={
        "version":"V106.1",
        "status":"pass" if not failures else "partial",
        "checks":checks,
        "no_external_api": os.environ.get("NO_EXTERNAL_API")=="true",
        "no_real_payment": os.environ.get("NO_REAL_PAYMENT")=="true",
        "no_real_send": os.environ.get("NO_REAL_SEND")=="true",
        "no_real_device": os.environ.get("NO_REAL_DEVICE")=="true",
        "remaining_failures":failures,
    }
    write_json("V106_1_CONTEXT_LAZY_SKILL_QUALITY_GATE.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1
if __name__ == "__main__":
    raise SystemExit(main())
