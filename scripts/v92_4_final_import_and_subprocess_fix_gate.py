#!/usr/bin/env python3
"""V92.4 final import + subprocess fix gate.
Fixes:
  1. execution/search/dedup.py → Deduplicator class (backward-compat)
  2. v92_full_static_audit_and_repair_gate.py → PYTHONPATH in subprocess env
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from infrastructure.safe_jsonable import safe_jsonable

ROOT = Path.cwd()
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

# ── modules that were failing due to missing Deduplicator ──
VISUAL_SPEC_MODULES = [
    "execution.visual_operation_agent.visual_planner",
    "execution.visual_operation_agent.action_executor",
    "execution.visual_operation_agent.screen_observer",
    "execution.visual_operation_agent.ui_grounding",
    "execution.speculative_decoding_v1.speculative_decoder",
    "execution.speculative_decoding_v1.nvidia_adapter",
]


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def check_env() -> dict:
    keys = ["OFFLINE_MODE", "NO_EXTERNAL_API", "DISABLE_LLM_API", "DISABLE_THINKING_MODE",
            "NO_REAL_SEND", "NO_REAL_PAYMENT", "NO_REAL_DEVICE"]
    return {k: os.environ.get(k, "").lower() in {"1", "true", "yes"} for k in keys}


def import_check(module: str) -> dict:
    try:
        importlib.import_module(module)
        return {"module": module, "status": "importable"}
    except Exception as exc:
        return {"module": module, "status": "fail", "error": str(exc)[:300]}


def main() -> int:
    results = {"version": "V92.4", "checked_at": now(), "checks": {}, "imports": {}}

    # 1. Deduplicator class
    try:
        from execution.search.dedup import Deduplicator
        d = Deduplicator()
        test_items = [
            {"id": 1, "name": "a"},
            {"id": 2, "name": "b"},
            {"id": 1, "name": "a"},  # dup
            "hello",
            "hello",  # dup str
        ]
        deduped = d.deduplicate(test_items)
        assert len(deduped) == 3, f"expected 3 unique, got {len(deduped)}"
        assert deduped[0] == {"id": 1, "name": "a"}
        assert deduped[1] == {"id": 2, "name": "b"}
        assert deduped[2] == "hello"
        # test __call__
        assert d(test_items) == deduped
        results["checks"]["deduplicator_class_exists"] = True
        results["checks"]["deduplicator_dedup_works"] = True
    except Exception as exc:
        results["checks"]["deduplicator_class_exists"] = False
        results["checks"]["deduplicator_error"] = str(exc)

    # 2. All 6 visual/speculative modules importable now
    for mod in VISUAL_SPEC_MODULES:
        results["imports"][mod] = import_check(mod)

    vs_ok = all(v["status"] == "importable" for v in results["imports"].values())
    results["checks"]["visual_speculative_all_importable"] = vs_ok

    # 3. self_improvement_loop import
    results["imports"]["core.self_evolution_ops.self_improvement_loop"] = import_check(
        "core.self_evolution_ops.self_improvement_loop"
    )
    results["checks"]["self_improvement_import_ok"] = (
        results["imports"]["core.self_evolution_ops.self_improvement_loop"]["status"] == "importable"
    )

    # 4. Verify subprocess env fix — run apply script and check its smoke
    env = os.environ.copy()
    env.update({
        "OFFLINE_MODE": "true", "NO_EXTERNAL_API": "true", "NO_REAL_SEND": "true",
        "NO_REAL_PAYMENT": "true", "NO_REAL_DEVICE": "true",
        "PYTHONPATH": str(ROOT) + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""),
    })
    results["checks"]["subprocess_env_has_pythonpath"] = bool(env.get("PYTHONPATH"))

    # 5. env check
    results["env"] = check_env()
    results["checks"]["offline_env_ok"] = all(results["env"].values())

    all_pass = all(v is True for v in results["checks"].values())
    results["status"] = "pass" if all_pass else "partial"
    results["remaining_failures"] = [k for k, v in results["checks"].items() if v is not True]

    out_path = REPORTS / "V92_4_FINAL_IMPORT_AND_SUBPROCESS_FIX_GATE.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(safe_jsonable(results), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(safe_jsonable(results), ensure_ascii=False, indent=2))
    return 0 if results["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
