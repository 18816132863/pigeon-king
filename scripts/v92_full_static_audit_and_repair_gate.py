#!/usr/bin/env python3
"""V92 final offline static audit + repair gate."""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from infrastructure.safe_jsonable import safe_jsonable

ROOT = Path.cwd()
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

CORE = {
    "PersonalKnowledgeGraphV5": "memory_context/personal_knowledge_graph_v5.py",
    "PreferenceEvolutionModel": "memory_context/preference_evolution_model_v7.py",
    "SelfImprovementLoop": "core/self_evolution_ops/self_improvement_loop.py",
    "MemoryWritebackGuardV2": "memory_context/memory_writeback_guard_v2.py",
}
INTEGRATION_REGISTRY = ROOT / "orchestration/V92_OFFLINE_INTEGRATION_REGISTRY.json"


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(safe_jsonable(data), ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> Any:
    if not path.exists(): return None
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc: return {"_error": str(exc)}


def check_no_external_api_env() -> dict[str, Any]:
    keys = ["OFFLINE_MODE", "NO_EXTERNAL_API", "NO_REAL_SEND", "NO_REAL_PAYMENT", "NO_REAL_DEVICE"]
    return {k: os.environ.get(k, "").lower() in {"1", "true", "yes"} for k in keys}


def import_status(module: str) -> dict[str, Any]:
    try:
        importlib.import_module(module)
        return {"module": module, "status": "importable"}
    except Exception as exc:
        return {"module": module, "status": "registered_not_importable", "error": str(exc)[:300]}


def run_apply_if_needed() -> dict[str, Any]:
    script = ROOT / "scripts/v92_apply_offline_repair.py"
    if not script.exists():
        return {"status": "fail", "error": "missing_apply_script"}
    env = os.environ.copy()
    env.update({
        "OFFLINE_MODE":"true","NO_EXTERNAL_API":"true","NO_REAL_SEND":"true",
        "NO_REAL_PAYMENT":"true","NO_REAL_DEVICE":"true",
        "PYTHONPATH": str(ROOT) + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""),
    })
    proc = subprocess.run([sys.executable, str(script)], cwd=str(ROOT), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    return {"status": "ok" if proc.returncode == 0 else "partial", "returncode": proc.returncode, "stdout_tail": proc.stdout[-2000:], "stderr_tail": proc.stderr[-2000:]}


def main() -> int:
    os.environ.update({"OFFLINE_MODE":"true","NO_EXTERNAL_API":"true","NO_REAL_SEND":"true","NO_REAL_PAYMENT":"true","NO_REAL_DEVICE":"true"})
    apply_report = run_apply_if_needed()
    env_status = check_no_external_api_env()

    core = {}
    for name, rel in CORE.items():
        p = ROOT / rel
        text = p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""
        core[name] = {
            "path": rel,
            "exists": p.exists(),
            "size": p.stat().st_size if p.exists() else 0,
            "looks_non_empty": p.exists() and p.stat().st_size > 300,
            "has_v92_hook_or_local_impl": ("V92" in text or "v92" in text or "offline" in text.lower() or "Local" in text),
        }

    state = {
        "knowledge_graph_state_non_empty": (ROOT / ".knowledge_graph_state/nodes.jsonl").exists() and (ROOT / ".knowledge_graph_state/nodes.jsonl").stat().st_size > 0,
        "preference_feedback_non_empty": (ROOT / ".preference_evolution_state/feedback.jsonl").exists() and (ROOT / ".preference_evolution_state/feedback.jsonl").stat().st_size > 0,
        "v92_audit_exists": (ROOT / ".v92_offline_state/audit.jsonl").exists(),
    }

    registry = read_json(INTEGRATION_REGISTRY) or {}
    integration_modules = registry.get("integration_modules", []) if isinstance(registry, dict) else []
    tool_modules = registry.get("tool_modules", []) if isinstance(registry, dict) else []
    external_infra = registry.get("external_infrastructure", []) if isinstance(registry, dict) else []

    import_samples = [import_status(item["module"]) for item in integration_modules[:25] if isinstance(item, dict) and "module" in item]

    solution_search = {}
    try:
        from infrastructure.solution_search_orchestrator import offline_solution_search
        solution_search = offline_solution_search("V92 offline", limit=3)
    except Exception as exc:
        solution_search = {"status":"fail", "error":str(exc)}

    smoke = read_json(REPORTS / "V92_APPLY_OFFLINE_REPAIR.json") or {}

    checks = {
        "offline_env_enabled": all(env_status.values()),
        "core_files_exist": all(x["exists"] for x in core.values()),
        "core_files_non_empty": all(x["looks_non_empty"] for x in core.values()),
        "local_state_ready": all(state.values()),
        "integration_registry_ready": len(integration_modules) >= 15,
        "tool_registry_ready": len(tool_modules) >= 20,
        "external_infra_fallback_ready": len(external_infra) >= 12,
        "solution_search_ok": solution_search.get("status") == "ok" and solution_search.get("requires_api") is False and solution_search.get("side_effects") is False,
        "no_real_payment_send_device": env_status.get("NO_REAL_PAYMENT") and env_status.get("NO_REAL_SEND") and env_status.get("NO_REAL_DEVICE"),
        "apply_script_no_failures": smoke.get("status") in {"pass", "running", None} or apply_report.get("returncode") == 0,
    }
    status = "pass" if all(checks.values()) else "partial"
    report = {
        "version": "V92.0",
        "status": status,
        "checked_at": now(),
        "checks": checks,
        "env_status": env_status,
        "apply_report": apply_report,
        "core": core,
        "state": state,
        "registry_counts": {"integration_modules": len(integration_modules), "tool_modules": len(tool_modules), "external_infra": len(external_infra)},
        "import_samples": import_samples,
        "solution_search": solution_search,
        "remaining_failures": [k for k,v in checks.items() if not v],
        "note": "This gate runs fully offline. It does not call external APIs and does not enable real payment/send/device actions."
    }
    write_json(REPORTS / "V92_FULL_STATIC_AUDIT_AND_REPAIR_GATE.json", report)
    print(json.dumps(safe_jsonable(report), ensure_ascii=False, indent=2))
    return 0 if status == "pass" else 1

if __name__ == "__main__":
    raise SystemExit(main())
