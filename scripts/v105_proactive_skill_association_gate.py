#!/usr/bin/env python3
from __future__ import annotations
import json, os, importlib
from pathlib import Path

ROOT = Path.cwd()
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

def write(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    failures = []
    checks = {}
    registry = ROOT / "governance" / "skill_trigger_registry.json"
    rules = ROOT / "docs" / "SKILL_ACCESS_RULES.md"
    matcher_file = ROOT / "governance" / "proactive_skill_matcher.py"

    checks["registry_exists"] = registry.exists()
    checks["rules_exists"] = rules.exists()
    checks["matcher_exists"] = matcher_file.exists()
    for k, v in checks.items():
        if not v:
            failures.append(k)

    try:
        data = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else {}
        items = list(data.values()) if isinstance(data, dict) else data
        total = len(items)
        context_count = sum(1 for x in items if isinstance(x, dict) and x.get("context_triggers"))
        scenario_count = sum(1 for x in items if isinstance(x, dict) and x.get("proactive_scenario"))
    except Exception as e:
        total = context_count = scenario_count = 0
        failures.append(f"registry_read_error:{e}")

    try:
        m = importlib.import_module("governance.proactive_skill_matcher")
        checks["matcher_importable"] = True
        samples = {
            "json_code": m.suggest_skills("这段 JSON 报错了，帮我看看格式和字段"),
            "excel_data": m.suggest_skills("我这里有一堆表格数据，想分析一下趋势"),
            "architecture": m.suggest_skills("我在整理系统架构和模块联动，看看哪些该融合"),
            "payment_block": m.suggest_skills("帮我下单付款并发送确认邮件"),
        }
    except Exception as e:
        checks["matcher_importable"] = False
        samples = {"error": str(e)}
        failures.append("matcher_import_failed")

    checks["context_trigger_coverage_ok"] = total > 0 and context_count >= int(total * 0.8)
    checks["proactive_scenario_coverage_ok"] = total > 0 and scenario_count >= int(total * 0.8)
    if not checks["context_trigger_coverage_ok"]:
        failures.append("context_trigger_coverage_low")
    if not checks["proactive_scenario_coverage_ok"]:
        failures.append("proactive_scenario_coverage_low")

    # samples quality
    sample_ok = True
    if isinstance(samples, dict) and "error" not in samples:
        sample_ok = all(v.get("status") == "ok" for v in samples.values())
        # payment sample should be marked commit_context, not auto execution
        sample_ok = sample_ok and samples["payment_block"].get("commit_context") is True
    else:
        sample_ok = False
    checks["sample_matching_ok"] = sample_ok
    if not sample_ok:
        failures.append("sample_matching_failed")

    report = {
        "version": "V105.0",
        "status": "pass" if not failures else "partial",
        "checks": checks,
        "registry_total": total,
        "context_trigger_count": context_count,
        "proactive_scenario_count": scenario_count,
        "sample_results": samples,
        "no_external_api": os.environ.get("NO_EXTERNAL_API") == "true",
        "no_real_payment": os.environ.get("NO_REAL_PAYMENT") == "true",
        "no_real_send": os.environ.get("NO_REAL_SEND") == "true",
        "no_real_device": os.environ.get("NO_REAL_DEVICE") == "true",
        "remaining_failures": failures,
    }
    write(REPORTS / "V105_PROACTIVE_SKILL_ASSOCIATION_GATE.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
