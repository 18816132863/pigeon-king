"""V104.3 Runtime Bus.

Coordinates mainline_hook, single_runtime_entrypoint, skill policy, runtime guard and commit barrier.
This is a lightweight coordination layer, not a new orchestrator. It records events and provides
one normalized dispatch surface for dry-run/pending-access tasks.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
AUDIT = ROOT / "governance" / "audit" / "runtime_bus.jsonl"
REPORTS.mkdir(exist_ok=True)
AUDIT.parent.mkdir(parents=True, exist_ok=True)


def _safe_json(obj: Any):
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _safe_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_safe_json(x) for x in obj]
    if hasattr(obj, "to_dict"):
        try:
            return _safe_json(obj.to_dict())
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        try:
            return _safe_json(vars(obj))
        except Exception:
            pass
    return str(obj)


def record_event(event: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"ts": time.time(), **event}
    try:
        with AUDIT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(_safe_json(payload), ensure_ascii=False) + "\n")
    except Exception as e:
        payload["audit_warning"] = str(e)
    return payload


def activate_guard(reason: str = "runtime_bus") -> Dict[str, Any]:
    try:
        from infrastructure.offline_runtime_guard import activate, status
        result = activate(reason=reason)
        st = status()
        return {"status": "ok", "activate": result, "guard_status": st}
    except Exception as e:
        return {"status": "warning", "error": str(e)}


def dispatch(goal: str = "", payload: Any = None, source: str = "runtime_bus", module: str | None = None) -> Dict[str, Any]:
    guard = activate_guard("runtime_bus.dispatch")
    try:
        from governance.runtime_commit_barrier_bridge import check_action
        barrier = check_action(goal=goal, payload=payload, source=source)
    except Exception as e:
        barrier = {"status": "warning", "error": str(e), "commit_blocked": False}

    if barrier.get("commit_blocked"):
        out = {
            "status": "blocked",
            "mode": "commit_barrier",
            "goal": goal,
            "source": source,
            "module": module,
            "runtime_guard": guard,
            "barrier": barrier,
            "side_effects": False,
            "external_api_calls": 0,
            "real_side_effects": 0,
        }
        record_event({"event": "dispatch_blocked", **out})
        return out

    hook_summary = None
    try:
        from infrastructure import mainline_hook
        if hasattr(mainline_hook, "run"):
            hook_summary = mainline_hook.run(message=str(payload or "")[:200], goal=goal, mode="runtime_bus")
    except Exception as e:
        hook_summary = {"status": "warning", "error": str(e)}

    entry_summary = None
    try:
        from orchestration import single_runtime_entrypoint
        if hasattr(single_runtime_entrypoint, "run") and source != "single_runtime_entrypoint":
            entry_summary = single_runtime_entrypoint.run(goal=goal, payload=payload, source="runtime_bus")
    except Exception as e:
        entry_summary = {"status": "warning", "error": str(e)}

    out = {
        "status": "ok",
        "mode": "offline_dry_run",
        "goal": goal,
        "source": source,
        "module": module,
        "runtime_guard": guard,
        "barrier": barrier,
        "mainline_hook": hook_summary,
        "single_runtime_entrypoint": entry_summary,
        "side_effects": False,
        "external_api_calls": 0,
        "real_side_effects": 0,
    }
    record_event({"event": "dispatch_ok", **out})
    return out


def summarize() -> Dict[str, Any]:
    lines = []
    if AUDIT.exists():
        try:
            lines = AUDIT.read_text(encoding="utf-8", errors="ignore").splitlines()[-50:]
        except Exception:
            lines = []
    return {
        "status": "ok",
        "audit_path": str(AUDIT),
        "recent_events": len(lines),
        "runtime_bus_linked": True,
        "no_external_api": os.environ.get("NO_EXTERNAL_API") == "true",
        "no_real_payment": os.environ.get("NO_REAL_PAYMENT") == "true",
        "no_real_send": os.environ.get("NO_REAL_SEND") == "true",
        "no_real_device": os.environ.get("NO_REAL_DEVICE") == "true",
    }
