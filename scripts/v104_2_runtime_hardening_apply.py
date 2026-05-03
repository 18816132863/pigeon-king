#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, shutil, time
from pathlib import Path

ROOT = Path.cwd()
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def patch_file_once(path: Path, marker: str, injection: str, after_pattern: str | None = None) -> dict:
    if not path.exists():
        return {"path": str(path.relative_to(ROOT)), "exists": False, "changed": False}
    s = path.read_text(encoding="utf-8", errors="ignore")
    if marker in s:
        return {"path": str(path.relative_to(ROOT)), "exists": True, "changed": False, "already": True}
    original = s
    if after_pattern and re.search(after_pattern, s, flags=re.M):
        s = re.sub(after_pattern, lambda m: m.group(0) + "\n" + injection, s, count=1, flags=re.M)
    else:
        s = injection + "\n" + s
    path.write_text(s, encoding="utf-8")
    return {"path": str(path.relative_to(ROOT)), "exists": True, "changed": s != original}


def patch_mainline_hook() -> dict:
    p = ROOT / "infrastructure" / "mainline_hook.py"
    inj = '''\n# V104_2_OFFLINE_RUNTIME_GUARD\ndef _v104_2_activate_offline_guard():\n    try:\n        from infrastructure.offline_runtime_guard import activate\n        return activate(reason="mainline_hook")\n    except Exception as e:\n        return {"status": "warning", "error": str(e)}\n\n_V104_2_OFFLINE_GUARD_STATUS = _v104_2_activate_offline_guard()\n'''
    return patch_file_once(p, "V104_2_OFFLINE_RUNTIME_GUARD", inj, after_pattern=r"^ROOT\s*=.*$")


def ensure_mainline_run_wrapper() -> dict:
    p = ROOT / "infrastructure" / "mainline_hook.py"
    if not p.exists():
        return {"path": str(p.relative_to(ROOT)), "exists": False, "changed": False, "run_ready": False}
    s = p.read_text(encoding="utf-8", errors="ignore")
    if re.search(r"^def\s+run\s*\(", s, flags=re.M):
        return {"path": str(p.relative_to(ROOT)), "exists": True, "changed": False, "run_ready": True}
    wrapper = '''

# V104_2_MAINLINE_RUN_WRAPPER
def run(message=None, goal=None, mode="pre_reply", **kwargs):
    """Compatibility wrapper expected by V98+/V100 gates.

    It delegates to pre_reply and returns a JSON-like dictionary.
    Fail-soft: never raises to caller.
    """
    try:
        if goal:
            try:
                set_last_goal(str(goal))
            except Exception:
                pass
        result = pre_reply(goal=goal, message=message)
        payload = result.to_dict() if hasattr(result, "to_dict") else safe_jsonable(result)
        if isinstance(payload, dict):
            payload.setdefault("status", "ok")
            payload.setdefault("mode", mode)
            payload.setdefault("fail_soft", True)
            payload.setdefault("heavy_chain_triggered", False)
        return payload
    except Exception as e:
        return {
            "status": "warning",
            "mode": mode,
            "fail_soft": True,
            "error": str(e),
            "heavy_chain_triggered": False,
            "context_summary": {},
            "guardrail_summary": {
                "no_external_api": os.environ.get("NO_EXTERNAL_API") == "true",
                "no_real_payment": os.environ.get("NO_REAL_PAYMENT") == "true",
                "no_real_send": os.environ.get("NO_REAL_SEND") == "true",
                "no_real_device": os.environ.get("NO_REAL_DEVICE") == "true",
            },
        }
'''
    p.write_text(s + wrapper, encoding="utf-8")
    return {"path": str(p.relative_to(ROOT)), "exists": True, "changed": True, "run_ready": True}


def patch_single_runtime() -> dict:
    p = ROOT / "orchestration" / "single_runtime_entrypoint.py"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('''from __future__ import annotations\n\n# V104_2_OFFLINE_RUNTIME_GUARD\ndef _v104_2_activate_offline_guard():\n    try:\n        from infrastructure.offline_runtime_guard import activate\n        return activate(reason="single_runtime_entrypoint")\n    except Exception as e:\n        return {"status": "warning", "error": str(e)}\n\n_V104_2_OFFLINE_GUARD_STATUS = _v104_2_activate_offline_guard()\n\ndef dispatch(goal=None, payload=None, mode="dry_run"):\n    return {\n        "status": "ok",\n        "mode": mode,\n        "goal": goal,\n        "payload": payload or {},\n        "offline_guard": _V104_2_OFFLINE_GUARD_STATUS,\n        "side_effects": False,\n        "gateway_required": True,\n    }\n''', encoding="utf-8")
        return {"path": str(p.relative_to(ROOT)), "exists": True, "changed": True, "created": True}
    inj = '''\n# V104_2_OFFLINE_RUNTIME_GUARD\ndef _v104_2_activate_offline_guard():\n    try:\n        from infrastructure.offline_runtime_guard import activate\n        return activate(reason="single_runtime_entrypoint")\n    except Exception as e:\n        return {"status": "warning", "error": str(e)}\n\n_V104_2_OFFLINE_GUARD_STATUS = _v104_2_activate_offline_guard()\n'''
    return patch_file_once(p, "V104_2_OFFLINE_RUNTIME_GUARD", inj)


def scan_direct_external_calls() -> dict:
    patterns = {
        "requests": r"requests\.",
        "urllib_urlopen": r"urllib\.request\.urlopen|urlretrieve\(",
        "httpx": r"httpx\.",
        "openai_like": r"\bopenai\b|\banthropic\b|\bdashscope\b",
        "git_push": r"git\s+push|subprocess\.run\([^\n]*push",
    }
    items = []
    for p in ROOT.rglob("*.py"):
        rel = str(p.relative_to(ROOT))
        if any(part in rel for part in ["__pycache__", ".pytest_cache", "reports/vintage", "archive/runtime_backups"]):
            continue
        try:
            s = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        hits = [name for name, pat in patterns.items() if re.search(pat, s, flags=re.I | re.S)]
        if hits:
            items.append({"path": rel, "markers": hits})
    report = {
        "version": "V104.2",
        "direct_external_call_files": len(items),
        "items": items[:500],
        "note": "Files may contain direct external calls. V104.2 adds runtime guard enforcement; future cleanup may patch individual modules when they become active.",
    }
    write_json(REPORTS / "V104_2_DIRECT_EXTERNAL_CALL_AUDIT.json", report)
    return report


def clean_runtime_artifacts() -> dict:
    removed = []
    moved = []
    for name in [".pytest_cache"]:
        p = ROOT / name
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
            removed.append(name)
    for p in list(ROOT.rglob("__pycache__")):
        shutil.rmtree(p, ignore_errors=True)
        removed.append(str(p.relative_to(ROOT)))
    archive = ROOT / "archive" / "runtime_backups"
    archive.mkdir(parents=True, exist_ok=True)
    for p in list(ROOT.glob(".backup_*")) + list(ROOT.glob(".repair_state")) + list(ROOT.glob("v86_backup_*")) + list(ROOT.glob(".v104_1_backup")):
        if p.exists():
            dest = archive / p.name
            if dest.exists():
                dest = archive / f"{p.name}_{int(time.time())}"
            try:
                shutil.move(str(p), str(dest))
                moved.append({"old": p.name, "new": str(dest.relative_to(ROOT))})
            except Exception:
                pass
    report = {"version": "V104.2", "removed": removed, "moved": moved, "cleaned": True}
    write_json(REPORTS / "V104_2_RUNTIME_ARTIFACT_CLEANUP_REPORT.json", report)
    return report


def main():
    results = {
        "version": "V104.2",
        "mainline_hook_patch": patch_mainline_hook(),
        "mainline_run_wrapper": ensure_mainline_run_wrapper(),
        "single_runtime_patch": patch_single_runtime(),
        "direct_external_call_audit": scan_direct_external_calls(),
        "runtime_artifact_cleanup": clean_runtime_artifacts(),
    }
    results["status"] = "pass"
    write_json(REPORTS / "V104_2_RUNTIME_HARDENING_APPLY.json", results)
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
