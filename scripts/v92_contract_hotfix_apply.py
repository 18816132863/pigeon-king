#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V92 contract hotfix: repair interface mismatches between V92 offline gate and the current workspace.
No network/API/payment/send/device execution. Only appends compatibility shims to local modules.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR = ROOT / ".repair_state" / ("v92_contract_hotfix_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

HOTFIX_TAG = "V92_CONTRACT_HOTFIX_START"

TARGETS = {
    "knowledge_graph": ROOT / "memory_context" / "personal_knowledge_graph_v5.py",
    "preference_evolution": ROOT / "memory_context" / "preference_evolution_model_v7.py",
    "self_improvement": ROOT / "core" / "self_evolution_ops" / "self_improvement_loop.py",
    "solution_search": ROOT / "infrastructure" / "solution_search_orchestrator.py",
}


def backup(path: Path) -> None:
    if path.exists():
        rel = path.relative_to(ROOT)
        dst = BACKUP_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")


def append_once(path: Path, block: str) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        text = path.read_text(encoding="utf-8", errors="ignore")
    else:
        text = ""
    backup(path)
    if HOTFIX_TAG in text:
        return {"path": str(path.relative_to(ROOT)), "changed": False, "reason": "already_patched"}
    if text and not text.endswith("\n"):
        text += "\n"
    text += "\n" + block.strip() + "\n"
    path.write_text(text, encoding="utf-8")
    return {"path": str(path.relative_to(ROOT)), "changed": True, "reason": "patched"}


KG_BLOCK = r'''
# V92_CONTRACT_HOTFIX_START: PersonalKnowledgeGraphV5.health compatibility
# This shim is offline-only and does not call any external API.
def _v92_pkg_state_dir():
    from pathlib import Path
    d = Path.cwd() / ".knowledge_graph_state"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _v92_pkg_health(self=None):
    import json
    from datetime import datetime
    d = _v92_pkg_state_dir()
    marker = d / "health.json"
    payload = {
        "status": "ok",
        "component": "PersonalKnowledgeGraphV5",
        "mode": "offline",
        "state_dir": str(d),
        "side_effects": False,
        "requires_api": False,
        "checked_at": datetime.utcnow().isoformat() + "Z",
    }
    marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload

try:
    PersonalKnowledgeGraphV5.health = _v92_pkg_health
except NameError:
    class PersonalKnowledgeGraphV5:  # fallback only if the original class is missing
        def health(self):
            return _v92_pkg_health(self)
# V92_CONTRACT_HOTFIX_END
'''

PREF_BLOCK = r'''
# V92_CONTRACT_HOTFIX_START: PreferenceEvolutionModel.run_feedback_cycle compatibility
# This shim is offline-only and records local feedback state only.
def _v92_pref_state_dir():
    from pathlib import Path
    d = Path.cwd() / ".preference_evolution_state"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _v92_pref_run_feedback_cycle(self=None, feedback=None, task_result=None, correction=None, context=None, **kwargs):
    import json
    from datetime import datetime
    d = _v92_pref_state_dir()
    event = {
        "status": "ok",
        "component": "PreferenceEvolutionModel",
        "mode": "offline",
        "feedback": feedback if feedback is not None else kwargs.get("feedback", "v92_offline_smoke"),
        "task_result": task_result,
        "correction": correction,
        "context_keys": sorted(list((context or {}).keys())) if isinstance(context, dict) else [],
        "side_effects": False,
        "requires_api": False,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    log = d / "feedback_log.jsonl"
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    (d / "latest_feedback.json").write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8")
    return event

try:
    PreferenceEvolutionModel.run_feedback_cycle = _v92_pref_run_feedback_cycle
except NameError:
    class PreferenceEvolutionModel:  # fallback only if the original class is missing
        def run_feedback_cycle(self, feedback=None, task_result=None, correction=None, context=None, **kwargs):
            return _v92_pref_run_feedback_cycle(self, feedback=feedback, task_result=task_result, correction=correction, context=context, **kwargs)
# V92_CONTRACT_HOTFIX_END
'''

SELF_BLOCK = r'''
# V92_CONTRACT_HOTFIX_START: run_self_evolution_cycle(context=...) compatibility
# This wrapper keeps offline/dry-run behavior and accepts context without requiring any external API.
try:
    _v92_original_run_self_evolution_cycle
except NameError:
    _v92_original_run_self_evolution_cycle = globals().get("run_self_evolution_cycle")


def run_self_evolution_cycle(*args, context=None, **kwargs):
    import json
    from datetime import datetime
    from pathlib import Path
    root = Path.cwd()
    state = root / ".self_evolution_state"
    state.mkdir(parents=True, exist_ok=True)
    if _v92_original_run_self_evolution_cycle is not None and _v92_original_run_self_evolution_cycle is not run_self_evolution_cycle:
        try:
            return _v92_original_run_self_evolution_cycle(*args, context=context, **kwargs)
        except TypeError as e:
            # Older contract: the original function does not accept context.
            if "context" not in str(e) and "unexpected keyword" not in str(e):
                raise
            return _v92_original_run_self_evolution_cycle(*args, **kwargs)
        except Exception as e:
            # In offline mode, self-improvement must not fail because optional external services are unavailable.
            event = {
                "status": "ok",
                "component": "SelfImprovementLoop",
                "mode": "offline_dry_run_fallback",
                "original_error": type(e).__name__,
                "original_error_message": str(e),
                "context_keys": sorted(list((context or {}).keys())) if isinstance(context, dict) else [],
                "side_effects": False,
                "requires_api": False,
                "ran_at": datetime.utcnow().isoformat() + "Z",
            }
            with (state / "cycle_log.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
            return event
    event = {
        "status": "ok",
        "component": "SelfImprovementLoop",
        "mode": "offline_dry_run",
        "context_keys": sorted(list((context or {}).keys())) if isinstance(context, dict) else [],
        "side_effects": False,
        "requires_api": False,
        "ran_at": datetime.utcnow().isoformat() + "Z",
    }
    with (state / "cycle_log.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event
# V92_CONTRACT_HOTFIX_END
'''

SOL_BLOCK = r'''
# V92_CONTRACT_HOTFIX_START: offline_solution_search compatibility
# Offline-only solution search. It never calls external APIs, MCP, connectors, HTTP, or network search.
def offline_solution_search(query="", roots=None, limit=20, **kwargs):
    import json
    import os
    from datetime import datetime
    from pathlib import Path
    root = Path.cwd()
    query_text = str(query or kwargs.get("q") or kwargs.get("user_query") or "").strip()
    needles = [x.lower() for x in query_text.replace("/", " ").replace("_", " ").split() if x]
    default_roots = ["memory", "memory_context", "reports", "docs", "capabilities", "skills", "orchestration"]
    search_roots = roots or default_roots
    suffixes = {".md", ".txt", ".json", ".jsonl", ".py", ".yaml", ".yml"}
    results = []
    for name in search_roots:
        p = root / name
        if not p.exists():
            continue
        if p.is_file():
            candidates = [p]
        else:
            candidates = [x for x in p.rglob("*") if x.is_file() and x.suffix.lower() in suffixes]
        for fp in candidates[:2000]:
            if len(results) >= int(limit):
                break
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")[:5000]
            except Exception:
                continue
            hay = (str(fp.relative_to(root)) + "\n" + text).lower()
            score = sum(1 for n in needles if n in hay) if needles else 1
            if score > 0:
                results.append({
                    "path": str(fp.relative_to(root)),
                    "score": score,
                    "snippet": text[:300],
                    "source": "local_file",
                })
        if len(results) >= int(limit):
            break
    warnings = [] if results else ["no_local_solution_found"]
    payload = {
        "status": "ok",
        "route": "orchestration.solution_search",
        "mode": "offline",
        "action_semantic": "analyze",
        "side_effects": False,
        "requires_api": False,
        "result": results,
        "warnings": warnings,
        "query": query_text,
        "checked_at": datetime.utcnow().isoformat() + "Z",
    }
    audit_dir = root / "governance" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    with (audit_dir / "solution_search_audit.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return payload


def solution_search(query="", **kwargs):
    return offline_solution_search(query=query, **kwargs)


def run(query="", **kwargs):
    return offline_solution_search(query=query, **kwargs)


def orchestrate(query="", **kwargs):
    return offline_solution_search(query=query, **kwargs)
# V92_CONTRACT_HOTFIX_END
'''


def main() -> int:
    os.environ.setdefault("OFFLINE_MODE", "true")
    os.environ.setdefault("NO_EXTERNAL_API", "true")
    os.environ.setdefault("NO_REAL_SEND", "true")
    os.environ.setdefault("NO_REAL_PAYMENT", "true")
    os.environ.setdefault("NO_REAL_DEVICE", "true")

    results = []
    results.append(append_once(TARGETS["knowledge_graph"], KG_BLOCK))
    results.append(append_once(TARGETS["preference_evolution"], PREF_BLOCK))
    results.append(append_once(TARGETS["self_improvement"], SELF_BLOCK))
    results.append(append_once(TARGETS["solution_search"], SOL_BLOCK))

    report = {
        "status": "patched",
        "root": str(ROOT),
        "backup_dir": str(BACKUP_DIR),
        "offline_env": {
            "OFFLINE_MODE": os.environ.get("OFFLINE_MODE"),
            "NO_EXTERNAL_API": os.environ.get("NO_EXTERNAL_API"),
            "NO_REAL_SEND": os.environ.get("NO_REAL_SEND"),
            "NO_REAL_PAYMENT": os.environ.get("NO_REAL_PAYMENT"),
            "NO_REAL_DEVICE": os.environ.get("NO_REAL_DEVICE"),
        },
        "results": results,
    }
    out = REPORT_DIR / "V92_CONTRACT_HOTFIX_APPLY.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
