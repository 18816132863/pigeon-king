#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "core", "skills", "capabilities", "orchestration", "execution", "infrastructure",
    "memory_context", "platform_adapter", "governance", "scripts", "docs",
    "governance/policy/execution_autopilot.py",
    "governance/policy/risk_tier_matrix.py",
    "platform_adapter/runtime_state_store.py",
    "platform_adapter/timeout_circuit.py",
    "platform_adapter/capability_registry.py",
    "platform_adapter/recovery_manager.py",
    "platform_adapter/delivery_outbox.py",
    "platform_adapter/result_verifier.py",
    "platform_adapter/trace_recorder.py",
    "platform_adapter/replay_harness.py",
    "platform_adapter/snapshot_manager.py",
    "platform_adapter/self_healing_supervisor.py",
    "governance/audit/execution_audit_ledger.py",
    "agent_kernel/goal_compiler.py",
    "agent_kernel/task_graph.py",
    "agent_kernel/memory_kernel.py",
    "agent_kernel/unified_judge.py",
    "agent_kernel/world_interface.py",
    "agent_kernel/capability_extension.py",
    "agent_kernel/handoff_orchestrator.py",
    "agent_kernel/persona_kernel.py",
    "agent_kernel/autonomous_loop.py",
    "scripts/v14_0_to_v23_0_all_smoke.py",
    "infrastructure/context_resume.py",
    "scripts/resume_current_task.py",
    "scripts/context_resume_smoke.py",
    "docs/v23_context_resume/CONTEXT_RESUME_GUIDE.md",
]

def main() -> int:
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    cache_hits = []
    for p in ROOT.rglob("*"):
        if "__pycache__" in p.parts or p.name in (".pytest_cache",) or p.suffix in (".pyc", ".pyo"):
            cache_hits.append(str(p.relative_to(ROOT)))
            if len(cache_hits) >= 30:
                break

    report = {
        "release": "V10.9_to_V23.1_context_resume_full_merged",
        "root": str(ROOT),
        "required_paths_passed": not missing,
        "missing": missing,
        "cache_check_passed": not cache_hits,
        "cache_hits_sample": cache_hits,
        "next_command": "/usr/bin/python3 scripts/context_resume_smoke.py && /usr/bin/python3 scripts/v14_0_to_v23_0_all_smoke.py",
        "overall": "pass" if (not missing and not cache_hits) else "fail",
    }
    out = ROOT / "V10_9_TO_V23_0_FULL_GATE_REPORT.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["overall"] == "pass" else 1

if __name__ == "__main__":
    raise SystemExit(main())
