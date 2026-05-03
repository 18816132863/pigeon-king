#!/usr/bin/env python3
from __future__ import annotations
import os, json
from pathlib import Path

ROOT = Path.cwd()
REPORTS = ROOT / "reports"

def load_json(path):
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

def main():
    usage = load_json(REPORTS / "V93_MODULE_USAGE_LEDGER.json")
    dep = load_json(REPORTS / "V93_DEPENDENCY_FALLBACK_REPORT.json")
    apply = load_json(REPORTS / "V93_APPLY_UNUSED_AND_INCOMPLETE_REPAIR.json")

    failures = []
    if os.environ.get("NO_EXTERNAL_API") != "true":
        failures.append("NO_EXTERNAL_API_not_enabled")
    if os.environ.get("NO_REAL_PAYMENT") != "true":
        failures.append("NO_REAL_PAYMENT_not_enabled")
    if os.environ.get("NO_REAL_SEND") != "true":
        failures.append("NO_REAL_SEND_not_enabled")
    if os.environ.get("NO_REAL_DEVICE") != "true":
        failures.append("NO_REAL_DEVICE_not_enabled")
    if not usage or not usage.get("items"):
        failures.append("usage_ledger_missing")
    if not dep or dep.get("status") != "pass":
        failures.append("dependency_fallback_report_missing")
    if not apply or apply.get("status") != "pass":
        failures.append("apply_report_missing_or_failed")

    items = usage.get("items", []) if usage else []
    registered_count = len([x for x in items if x.get("registered")])
    dryrun_count = len([x for x in items if x.get("call_count", 0) >= 1])
    fallback_count = len([x for x in items if x.get("last_result") == "import_failed_fallback_registered"])

    report = {
        "version": "V93.0",
        "status": "pass" if not failures else "partial",
        "checks": {
            "no_external_api": os.environ.get("NO_EXTERNAL_API") == "true",
            "no_real_payment": os.environ.get("NO_REAL_PAYMENT") == "true",
            "no_real_send": os.environ.get("NO_REAL_SEND") == "true",
            "no_real_device": os.environ.get("NO_REAL_DEVICE") == "true",
            "usage_ledger_ready": bool(usage and usage.get("items")),
            "dependency_fallback_ready": bool(dep and dep.get("status") == "pass"),
            "apply_report_ready": bool(apply and apply.get("status") == "pass"),
        },
        "registered_count": registered_count,
        "dryrun_import_ok_count": dryrun_count,
        "fallback_registered_count": fallback_count,
        "remaining_failures": failures,
        "note": "V93 是使用率审计与离线 fallback 收口，不代表所有模块已生产级真实运行。"
    }

    (REPORTS / "V93_UNUSED_AND_INCOMPLETE_FUNCTION_GATE.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
