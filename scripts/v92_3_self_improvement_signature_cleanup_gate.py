#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import inspect
import json
import os
from pathlib import Path

ROOT = Path.cwd()
REPORT = ROOT / "reports" / "V92_3_SELF_IMPROVEMENT_SIGNATURE_CLEANUP_GATE.json"

def main():
    os.environ.setdefault("OFFLINE_MODE", "true")
    os.environ.setdefault("NO_EXTERNAL_API", "true")
    os.environ.setdefault("NO_REAL_SEND", "true")
    os.environ.setdefault("NO_REAL_PAYMENT", "true")
    os.environ.setdefault("NO_REAL_DEVICE", "true")
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    checks = []
    result = {"status": "fail", "checks": checks, "errors": []}

    try:
        mod = importlib.import_module("core.self_evolution_ops.self_improvement_loop")
        fn = getattr(mod, "run_self_evolution_cycle")
        sig = inspect.signature(fn)
        params = sig.parameters
        checks.append({"name": "import", "pass": True})
        checks.append({"name": "signature", "value": str(sig)})

        has_goal = "goal" in params
        checks.append({"name": "goal_parameter_exists", "pass": has_goal})
        goal_default = has_goal and params["goal"].default is not inspect._empty
        checks.append({"name": "goal_has_default", "pass": goal_default})
        not_args_signature = not any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params.values())
        checks.append({"name": "no_varargs_signature", "pass": not_args_signature})
        context_exists = "context" in params
        checks.append({"name": "context_parameter_exists", "pass": context_exists})

        try:
            out = fn(context={"gate": "v92_3_contract"})
            checks.append({"name": "context_only_call_no_typeerror", "pass": True, "result_type": type(out).__name__})
        except TypeError as e:
            checks.append({"name": "context_only_call_no_typeerror", "pass": False, "error": str(e)})
        except Exception as e:
            checks.append({"name": "context_only_call_no_typeerror", "pass": True, "non_type_error_ignored": str(e)})
    except Exception as e:
        checks.append({"name": "import", "pass": False, "error": str(e)})
        result["errors"].append(str(e))

    bool_checks = [c for c in checks if "pass" in c]
    result["passed"] = sum(1 for c in bool_checks if c.get("pass") is True)
    result["total"] = len(bool_checks)
    result["remaining_failures"] = [c for c in bool_checks if c.get("pass") is not True]
    result["status"] = "pass" if result["remaining_failures"] == [] else "partial"
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1

if __name__ == "__main__":
    raise SystemExit(main())
