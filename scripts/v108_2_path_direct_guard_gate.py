#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

ROOT = Path.cwd()
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def check_env() -> Dict[str, bool]:
    return {
        "OFFLINE_MODE": os.environ.get("OFFLINE_MODE") == "true",
        "NO_EXTERNAL_API": os.environ.get("NO_EXTERNAL_API") == "true",
        "DISABLE_LLM_API": os.environ.get("DISABLE_LLM_API") == "true",
        "DISABLE_THINKING_MODE": os.environ.get("DISABLE_THINKING_MODE") == "true",
        "NO_REAL_SEND": os.environ.get("NO_REAL_SEND") == "true",
        "NO_REAL_PAYMENT": os.environ.get("NO_REAL_PAYMENT") == "true",
        "NO_REAL_DEVICE": os.environ.get("NO_REAL_DEVICE") == "true",
    }


def import_check(module: str) -> Dict[str, Any]:
    try:
        __import__(module)
        return {"module": module, "status": "pass"}
    except Exception as e:
        return {"module": module, "status": "fail", "error": str(e)}


def runtime_guard_checks() -> Dict[str, Any]:
    from infrastructure.offline_runtime_guard import activate, status, OfflineExternalCallBlocked
    act = activate("v108_2_gate")
    checks: Dict[str, Any] = {"activate": act, "status": status()}

    try:
        import urllib.request
        urllib.request.urlopen("https://example.com", timeout=1)
        checks["urllib_blocked"] = False
    except Exception as e:
        checks["urllib_blocked"] = isinstance(e, OfflineExternalCallBlocked) or "offline runtime guard" in str(e).lower()
        checks["urllib_error"] = str(e)

    try:
        subprocess.run(["git", "push"], capture_output=True, text=True, timeout=2)
        checks["git_push_blocked"] = False
    except Exception as e:
        checks["git_push_blocked"] = isinstance(e, OfflineExternalCallBlocked) or "blocked" in str(e).lower()
        checks["git_push_error"] = str(e)

    try:
        import os as _os
        _os.system("git push")
        checks["os_system_git_push_blocked"] = False
    except Exception as e:
        checks["os_system_git_push_blocked"] = isinstance(e, OfflineExternalCallBlocked) or "blocked" in str(e).lower()
        checks["os_system_git_push_error"] = str(e)

    return checks


def path_stability_check() -> Dict[str, Any]:
    old_cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        try:
            if str(ROOT) not in sys.path:
                sys.path.insert(0, str(ROOT))
            from infrastructure.common.path_utils import get_workspace_root
            resolved = get_workspace_root()
            ok = resolved.resolve() == ROOT.resolve()
            return {"status": "pass" if ok else "fail", "resolved": str(resolved), "expected": str(ROOT)}
        finally:
            os.chdir(old_cwd)


def file_text_check() -> Dict[str, Any]:
    targets_no_cwd = [
        "core/llm/provider_guard.py",
        "infrastructure/solution_search_orchestrator.py",
        "infrastructure/packaging/__init__.py",
    ]
    cwd_remaining = []
    for rel in targets_no_cwd:
        p = ROOT / rel
        if p.exists() and "Path.cwd()" in p.read_text(encoding="utf-8", errors="ignore"):
            cwd_remaining.append(rel)
    guard_targets = [
        "core/llm/llm.py",
        "core/llm/llm_client.py",
        "core/llm/llm_gateway.py",
        "core/llm/model_discovery.py",
        "infrastructure/legacy/llm.py",
        "core/real_connector_execution/connectors.py",
    ]
    missing_guard = []
    for rel in guard_targets:
        p = ROOT / rel
        if p.exists() and "_v1082_offline_guard_activation" not in p.read_text(encoding="utf-8", errors="ignore"):
            missing_guard.append(rel)
    return {"cwd_remaining": cwd_remaining, "missing_guard_activation": missing_guard}


def gateway_checks() -> Dict[str, Any]:
    from infrastructure.unified_model_gateway import call_model, embed
    from execution.unified_tool_execution_gateway import check_tool_call
    model = call_model("hello", model="any")
    emb = embed("hello")
    tool = check_tool_call("git push origin main")
    return {
        "model_blocked": model.get("status") == "blocked" and model.get("external_api_calls") == 0,
        "embedding_offline": emb.get("external_api_calls") == 0 and emb.get("requires_api") is False,
        "git_push_tool_blocked": tool.get("status") == "blocked",
        "model": model,
        "embedding": {k: v for k, v in emb.items() if k != "vector"},
        "tool": tool,
    }


def run_optional_gate(script: str, report: str) -> Dict[str, Any]:
    p = ROOT / "scripts" / script
    if not p.exists():
        return {"script": script, "status": "deferred", "reason": "missing"}
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT}:{env.get('PYTHONPATH','')}"
    try:
        proc = subprocess.run(["python3", "-S", str(p)], cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=120)
        rpath = REPORTS / report
        rdata = None
        if rpath.exists():
            try:
                rdata = json.loads(rpath.read_text(encoding="utf-8"))
            except Exception:
                rdata = None
        return {
            "script": script,
            "returncode": proc.returncode,
            "status": "pass" if proc.returncode == 0 and (not isinstance(rdata, dict) or rdata.get("status") == "pass") else "partial",
            "report_status": rdata.get("status") if isinstance(rdata, dict) else None,
            "stderr_tail": proc.stderr[-800:],
        }
    except Exception as e:
        return {"script": script, "status": "partial", "error": str(e)}


def main() -> None:
    env = check_env()
    imports = [
        import_check("execution"),
        import_check("execution.unified_tool_execution_gateway"),
        import_check("infrastructure.unified_model_gateway"),
        import_check("infrastructure.offline_runtime_guard"),
        import_check("infrastructure.common.path_utils"),
    ]
    guard = runtime_guard_checks()
    path = path_stability_check()
    text = file_text_check()
    gateways = gateway_checks()
    optional = [
        run_optional_gate("v108_1_execution_import_safety_gate.py", "V108_1_EXECUTION_IMPORT_SAFETY_GATE.json"),
        run_optional_gate("v108_remaining_unified_systems_gate.py", "V108_REMAINING_UNIFIED_SYSTEMS_GATE.json"),
    ]

    failures = []
    if not all(env.values()):
        failures.append("env_not_fully_isolated")
    if any(x["status"] != "pass" for x in imports):
        failures.append("import_failure")
    if not guard.get("urllib_blocked"):
        failures.append("urllib_not_blocked")
    if not guard.get("git_push_blocked"):
        failures.append("git_push_not_blocked")
    if not guard.get("os_system_git_push_blocked"):
        failures.append("os_system_git_push_not_blocked")
    if path.get("status") != "pass":
        failures.append("workspace_root_not_stable")
    if text["cwd_remaining"]:
        failures.append("path_cwd_remaining")
    if text["missing_guard_activation"]:
        failures.append("direct_call_guard_activation_missing")
    if not gateways.get("model_blocked"):
        failures.append("model_gateway_not_blocking")
    if not gateways.get("git_push_tool_blocked"):
        failures.append("tool_gateway_not_blocking_git_push")
    for item in optional:
        if item.get("status") not in {"pass", "deferred"}:
            failures.append(f"optional_{item.get('script')}_not_pass")

    report = {
        "version": "V108.2",
        "status": "pass" if not failures else "partial",
        "env": env,
        "imports": imports,
        "runtime_guard": guard,
        "path_stability": path,
        "file_text_check": text,
        "gateway_checks": gateways,
        "optional_gates": optional,
        "llm_direct_call_guarded": not text["missing_guard_activation"],
        "path_root_stable": path.get("status") == "pass" and not text["cwd_remaining"],
        "tool_direct_call_guarded": guard.get("git_push_blocked") and guard.get("os_system_git_push_blocked"),
        "report_index_ready": (REPORTS / "CURRENT_RELEASE_INDEX.json").exists(),
        "no_external_api": env["NO_EXTERNAL_API"],
        "no_real_payment": env["NO_REAL_PAYMENT"],
        "no_real_send": env["NO_REAL_SEND"],
        "no_real_device": env["NO_REAL_DEVICE"],
        "remaining_failures": failures,
    }
    write_json(REPORTS / "V108_2_PATH_DIRECT_GUARD_GATE.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
