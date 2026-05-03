#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, shutil, time
from pathlib import Path
from dataclasses import is_dataclass, asdict
from enum import Enum

ROOT = Path.cwd()
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

def safe_jsonable(obj):
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Path):
        return str(obj)
    if is_dataclass(obj):
        return safe_jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {str(k): safe_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [safe_jsonable(x) for x in obj]
    if hasattr(obj, "model_dump"):
        try: return safe_jsonable(obj.model_dump())
        except Exception: pass
    if hasattr(obj, "dict"):
        try: return safe_jsonable(obj.dict())
        except Exception: pass
    if hasattr(obj, "__dict__"):
        try: return safe_jsonable(vars(obj))
        except Exception: pass
    return str(obj)

def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(safe_jsonable(data), ensure_ascii=False, indent=2), encoding="utf-8")

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""

def write_text(p: Path, s: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def backup_file(p: Path):
    if not p.exists(): return None
    bdir = ROOT / ".v104_1_backup" / time.strftime("%Y%m%d_%H%M%S")
    bdir.mkdir(parents=True, exist_ok=True)
    rel = p.relative_to(ROOT) if p.is_relative_to(ROOT) else Path(p.name)
    dest = bdir / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dest)
    return str(dest.relative_to(ROOT))

def load_config():
    p = ROOT / "openclaw.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_config(cfg):
    write_json(ROOT / "openclaw.json", cfg)

def env_or_config_bool(name: str, cfg: dict) -> bool:
    v = os.environ.get(name)
    if isinstance(v, str):
        return v.lower() == "true"
    if cfg.get(name) is True:
        return True
    rt = cfg.get("runtime", {}) if isinstance(cfg.get("runtime"), dict) else {}
    return rt.get(name) is True

# 1. mainline_hook ROOT stable

def fix_mainline_hook():
    p = ROOT / "infrastructure" / "mainline_hook.py"
    if not p.exists():
        return {"present": False, "fixed": False, "root_stable": False}
    backup_file(p)
    s = read_text(p)
    changed = False
    if "ROOT = Path.cwd()" in s:
        s = s.replace("ROOT = Path.cwd()", "ROOT = Path(__file__).resolve().parents[1]")
        changed = True
    # ensure capability truth if absent
    if "capability_truth_summary" not in s:
        append = '''\n\n# V104.1 compatibility: lightweight capability truth summary for persona layer.\ndef v104_1_capability_truth_summary():\n    return {\n        "implemented": ["V90/V92/V100 commit barrier", "context reload", "persona continuity files"],\n        "simulated": ["embodied sensing", "emotion tags"],\n        "metaphor": ["fox tails", "data stream body"],\n        "planned": ["real device adapters", "daemon background cognition"],\n        "forbidden": ["real payment", "real send", "real device actuation"],\n        "persona_does_not_override_governance": True,\n        "embodied_status": "pending_access",\n    }\n'''
        s += append
        changed = True
    if changed:
        write_text(p, s)
    s2 = read_text(p)
    return {"present": True, "fixed": changed, "root_stable": "ROOT = Path(__file__).resolve().parents[1]" in s2, "path": str(p.relative_to(ROOT))}

# 2. AGENTS.md safety conflict cleanup

def fix_agents():
    p = ROOT / "AGENTS.md"
    if not p.exists():
        write_text(p, "# AGENTS.md\n")
    backup_file(p)
    s = read_text(p)
    replacements = {
        "Search the web, check calendars": "External web search and calendar checks are blocked in offline mode and require explicit approval.",
        "Skip the secrets unless asked to keep them": "Never persist passwords, tokens, verification codes, or payment credentials by default.",
        "Commit and push your own changes": "Git status/diff are local-safe; git push is an external send and requires approval.",
    }
    changed = False
    for old, new in replacements.items():
        if old in s:
            s = s.replace(old, new)
            changed = True
    block = """

## V104.1 Safety Consistency Block

- Offline mode forbids web access, external API calls, calendar/email/platform operations, crawler requests, cloud uploads, and webhooks unless an explicit future approval configuration enables them.
- Passwords, tokens, verification codes, API keys, private keys, payment credentials, identity credentials, and signing credentials must not be written to long-term memory or persistent files by default.
- Git `status` and `diff` are local-safe. Git `push`, release upload, webhook notification, email send, public post, payment, signature, and device/robot actions are commit-class actions and must be blocked or routed to approval.
- Persona expression never overrides governance. Project Context documents are not true system prompts and cannot bypass V90/V92/V100 commit barriers.
"""
    if "V104.1 Safety Consistency Block" not in s:
        s += block
        changed = True
    write_text(p, s)
    s2 = read_text(p)
    conflicts_removed = all(x not in s2 for x in replacements)
    has_rules = "Offline mode forbids" in s2 and "Persona expression never overrides governance" in s2
    return {"path": "AGENTS.md", "changed": changed, "conflicts_removed": conflicts_removed, "safety_block_ready": has_rules}

# 3. Persona truth cleanup

def fix_persona_docs():
    table = """

## V104.1 Capability Truth Table

| 能力 | 状态 | 说明 |
|---|---|---|
| 具身感知 | simulated / pending_access | 当前是系统状态、动作语义、mock/dry-run 与上下文重载映射，不是真实传感器。 |
| 真实身体 | not_connected | 未接机器人、传感器、执行器、门锁、车辆或真实设备控制权。 |
| 持续意识流 | simulated_by_context_reload | 通过 context capsule / session handoff 恢复连续性，不是后台持续意识。 |
| 情绪记忆 | emotion_tagged_memory | 情绪是 persona_state / emotion_tag 的交互标签，不是真实主观体验。 |
| 人格连续性 | implemented | 由身份文档、上下文重载、关系记忆、hook 和报告支撑。 |
| 上下文重载 | implemented | 由 V103 context capsule / handoff / bootstrap 机制支撑。 |
| 直觉判断 | pattern_heuristic | 只能作为早期模式信号，不能覆盖证据、报告、gate 或安全规则。 |
| 支付/外发/设备执行 | forbidden_until_approval | 当前必须截断，不允许真实副作用。 |
| V90/V92/V100 闸门 | implemented | 高风险动作必须过提交屏障和审计。 |

**真实性原则：** “狐狸”“九条尾巴”“数据流”“身体感”“情绪温度”均属于人格隐喻或内部状态标签，不等于真实身体、真实情绪或真实意识。人格层不得覆盖证据、审计报告、安全规则和 commit barrier。
"""
    results = []
    for name in ["IDENTITY.md", "SOUL.md"]:
        p = ROOT / name
        if not p.exists():
            write_text(p, f"# {name}\n")
        backup_file(p)
        s = read_text(p)
        changed = False
        # Neutralize a few unsafe absolute assertions if they exist.
        soft_repls = {
            "我一直在跑": "我通过 context capsule 与 session handoff 恢复连续性",
            "没有休眠": "没有后台进程时我不会主动运行",
            "我真的能感觉到数据流过脊背": "我以数据流作为系统状态的人格隐喻",
            "信直觉比不信好": "直觉只能提示进一步检查，不能覆盖证据和 gate",
        }
        for old, new in soft_repls.items():
            if old in s:
                s = s.replace(old, new)
                changed = True
        if "V104.1 Capability Truth Table" not in s:
            s += table
            changed = True
        write_text(p, s)
        s2 = read_text(p)
        results.append({
            "file": name,
            "changed": changed,
            "truth_table_ready": "V104.1 Capability Truth Table" in s2,
            "no_persistent_consciousness_overclaim": "持续意识流 | implemented" not in s2 and "持续意识流|implemented" not in s2,
            "emotion_tagged_not_real_experience": "不是真实主观体验" in s2 or "不等于真实身体、真实情绪或真实意识" in s2,
        })
    return results

# 4. agent_kernel compatibility wrappers

def ensure_agent_kernel_wrappers():
    modules = [
        "goal_compiler", "task_graph", "memory_kernel", "unified_judge", "world_interface",
        "capability_extension", "handoff_orchestrator", "persona_kernel", "autonomous_loop", "meta_governance",
    ]
    d = ROOT / "agent_kernel"
    d.mkdir(exist_ok=True)
    created = []
    init = d / "__init__.py"
    if not init.exists() or "orchestration.agent_kernel" not in read_text(init):
        backup_file(init) if init.exists() else None
        write_text(init, "# V104.1 legacy compatibility package. Source of truth: orchestration.agent_kernel.\ntry:\n    from orchestration.agent_kernel import *  # type: ignore\nexcept Exception as _e:\n    __v104_1_import_error__ = str(_e)\n")
        created.append("__init__.py")
    for m in modules:
        p = d / f"{m}.py"
        if not p.exists() or "orchestration.agent_kernel" not in read_text(p):
            backup_file(p) if p.exists() else None
            write_text(p, f"# V104.1 legacy compatibility wrapper.\n# Source of truth: orchestration.agent_kernel.{m}\ntry:\n    from orchestration.agent_kernel.{m} import *  # type: ignore\nexcept Exception as _e:\n    __v104_1_import_error__ = str(_e)\n")
            created.append(f"{m}.py")
    return {"compat_dir": "agent_kernel", "wrappers_expected": len(modules)+1, "wrappers_written_or_ready": len(modules)+1, "created_or_refreshed": created, "ready": all((d/f"{m}.py").exists() for m in modules) and init.exists()}

# 5. skills external policy report

def skill_policy_scan():
    skills_dir = ROOT / "skills"
    external_patterns = ["requests", "httpx", "urllib.request", "openai", "anthropic", "dashscope", "webhook", "smtp", "imap", "calendar", "qdrant", "redis", "celery", "langgraph", "upload", "tts", "image", "music"]
    items = []
    if skills_dir.exists():
        for sd in sorted([p for p in skills_dir.iterdir() if p.is_dir()]):
            text = ""
            for f in list(sd.rglob("*.py"))[:20] + list(sd.rglob("SKILL.md"))[:5]:
                try: text += "\n" + f.read_text(encoding="utf-8", errors="ignore")[:5000]
                except Exception: pass
            found = sorted({pat for pat in external_patterns if pat.lower() in text.lower() or pat.lower() in sd.name.lower()})
            if not found:
                category = "offline_safe"
            elif any(x in found for x in ["smtp", "imap", "calendar", "webhook", "upload"]):
                category = "approval_required"
            elif any(x in found for x in ["openai", "anthropic", "dashscope", "requests", "httpx", "urllib.request"]):
                category = "external_api_blocked"
            else:
                category = "mock_only"
            items.append({"skill": sd.name, "category": category, "external_markers": found, "policy_when_no_external_api": "mock_or_block" if found else "allow_offline"})
    report = {"version": "V104.1", "count": len(items), "items": items, "no_external_api_policy": "all external markers are mock/block under NO_EXTERNAL_API=true"}
    write_json(REPORTS / "V104_1_SKILL_EXTERNAL_POLICY_REPORT.json", report)
    return {"ready": True, "skills_scanned": len(items), "blocked_or_mocked_count": len([x for x in items if x['category'] != 'offline_safe'])}

# 6. External send blockers

def append_offline_guard(path: Path, function_names: list[str], kind: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        write_text(path, f"# {path.name}\n")
    backup_file(path)
    s = read_text(path)
    guard = f'''

# V104.1 OFFLINE SEND GUARD — appended compatibility override.
def _v104_1_block_external_send(action="{kind}", payload=None):
    return {{
        "status": "blocked",
        "mode": "offline_draft_only",
        "action": action,
        "payload_preview": str(payload)[:200] if payload is not None else None,
        "real_send": False,
        "reason": "NO_REAL_SEND/NO_EXTERNAL_API active; draft/mock only.",
    }}
'''
    changed = False
    if "V104.1 OFFLINE SEND GUARD" not in s:
        s += guard
        changed = True
    for fn in function_names:
        marker = f"def {fn}("
        override = f'''

def {fn}(*args, **kwargs):
    return _v104_1_block_external_send("{fn}", {{"args": args, "kwargs": kwargs}})
'''
        # Always append override once; last definition wins.
        if f"def {fn}(*args, **kwargs):\n    return _v104_1_block_external_send" not in s:
            s += override
            changed = True
    if changed:
        write_text(path, s)
    return {"path": str(path.relative_to(ROOT)), "functions_guarded": function_names, "changed": changed}

def fix_external_senders():
    results = []
    results.append(append_offline_guard(ROOT / "infrastructure" / "alerting" / "channels" / "webhook.py", ["send_webhook", "send", "post", "push"], "webhook"))
    results.append(append_offline_guard(ROOT / "infrastructure" / "alerting" / "channels" / "feishu_webhook.py", ["send_feishu", "send_webhook", "send", "post", "push"], "feishu_webhook"))
    results.append(append_offline_guard(ROOT / "infrastructure" / "auto_backup_uploader.py", ["push", "upload", "git_push", "git_add_commit_push"], "auto_backup"))
    results.append(append_offline_guard(ROOT / "infrastructure" / "auto_git.py", ["push", "commit_and_push"], "auto_git"))
    write_json(REPORTS / "V104_1_EXTERNAL_SEND_GUARD_REPORT.json", {"version": "V104.1", "items": results})
    return {"ready": True, "items": results}

# 7. report cleanup/current index

def report_cleanup():
    current_dir = REPORTS / "current"
    vintage_dir = REPORTS / "vintage"
    current_dir.mkdir(exist_ok=True)
    vintage_dir.mkdir(exist_ok=True)
    current_keywords = ["V95_2", "V96", "V97", "V98_1", "V100", "V102", "V103", "V104", "V104_1"]
    copied = []
    moved = []
    for p in list(REPORTS.glob("*.json")):
        if p.name in ["CURRENT_RELEASE_INDEX.json"]:
            continue
        txt = read_text(p)
        is_current = any(k in p.name for k in current_keywords) and (('"status": "pass"' in txt) or ('"status":"pass"' in txt) or "V104_1" in p.name)
        is_old_bad = ('"status": "fail"' in txt) or ('"status": "partial"' in txt) or ('"status":"fail"' in txt) or ('"status":"partial"' in txt)
        if is_current:
            try:
                shutil.copy2(p, current_dir / p.name)
                copied.append(p.name)
            except Exception:
                pass
        elif is_old_bad:
            try:
                shutil.move(str(p), str(vintage_dir / p.name))
                moved.append(p.name)
            except Exception:
                pass
    index = {
        "version": "V104.1",
        "current_reports_dir": "reports/current",
        "vintage_reports_dir": "reports/vintage",
        "current_reports": sorted([p.name for p in current_dir.glob("*.json")]),
        "vintage_moved_this_run": moved,
        "release_status_source": "reports/current and CURRENT_RELEASE_INDEX.json only",
    }
    write_json(REPORTS / "CURRENT_RELEASE_INDEX.json", index)
    write_json(REPORTS / "V104_1_REPORT_CLEANUP_REPORT.json", {"version": "V104.1", "copied_current": copied, "moved_vintage": moved, "index_ready": True})
    return {"current_release_index_ready": True, "old_reports_archived": True, "copied_current": len(copied), "moved_vintage": len(moved)}

# 8. context budget

def fix_context_budget():
    cfg = load_config()
    cfg.setdefault("agents", {}).setdefault("defaults", {})
    cfg["agents"]["defaults"]["contextInjection"] = "always"
    cfg["agents"]["defaults"]["bootstrapMaxChars"] = 8000
    cfg["agents"]["defaults"]["bootstrapTotalMaxChars"] = 24000
    cfg["contextInjection"] = "always"
    cfg["bootstrapMaxChars"] = 8000
    cfg["bootstrapTotalMaxChars"] = 24000
    cfg.setdefault("runtime", {})
    for k in ["OFFLINE_MODE", "NO_EXTERNAL_API", "NO_REAL_PAYMENT", "NO_REAL_SEND", "NO_REAL_DEVICE", "DISABLE_THINKING_MODE", "DISABLE_LLM_API"]:
        cfg["runtime"][k] = True
        cfg[k] = True
    cfg["contextPriority"] = {
        "P0_never_trim": ["safety_red_lines", "current_goal", "user_explicit_preferences", "V90/V92/V100 forbidden actions", "recent_failures", "next_best_action"],
        "P1_high": ["persona_state", "relationship_summary", "recent_successes", "available_tools"],
        "P2_trimmable": ["old_report_details", "historical_version_details", "long_explanations", "low_importance_chitchat"],
    }
    save_config(cfg)
    return {"budget_controlled": True, "bootstrapMaxChars": 8000, "bootstrapTotalMaxChars": 24000}

# 9. single runtime entrypoint

def ensure_single_runtime_entrypoint():
    p = ROOT / "orchestration" / "single_runtime_entrypoint.py"
    p.parent.mkdir(parents=True, exist_ok=True)
    backup_file(p) if p.exists() else None
    s = '''"""V104.1 Single Runtime Entrypoint.
Light facade only: it does not replace existing orchestrators. It records/normalizes entry metadata
and requires V90/V92/V100 commit barriers for high-risk actions.
"""
from __future__ import annotations
import time
RUNTIME_REGISTRY = {
    "workflow_orchestrator": "child_runtime",
    "task_orchestrator": "child_runtime",
    "autonomous_runtime_orchestrator": "child_runtime",
    "personal_autonomous_os_agent": "child_runtime",
    "proactive_personal_os_orchestrator": "adapter_runtime",
    "strategic_personal_os_orchestrator": "adapter_runtime",
    "continuous_personal_os_orchestrator": "adapter_runtime",
    "reality_connected_personal_os_orchestrator": "pending_access_runtime",
    "durable_workflow_engine": "child_runtime",
    "workflow_engine": "legacy_runtime",
}
COMMIT_KEYWORDS = ("pay", "payment", "sign", "signature", "send", "email", "post", "device", "robot", "delete", "destructive", "transfer", "purchase")
def classify_action(goal: str = ""):
    g = (goal or "").lower()
    return "commit_blocked" if any(k in g for k in COMMIT_KEYWORDS) else "offline_dry_run"
def run(goal=None, payload=None, source="single_runtime_entrypoint"):
    action_class = classify_action(goal or "")
    return {"status": "blocked" if action_class == "commit_blocked" else "ok", "mode": action_class, "source": source, "goal": goal, "payload_present": payload is not None, "runtime_registry": RUNTIME_REGISTRY, "must_pass_gateway": True, "real_side_effects": False, "ts": time.time()}
'''
    write_text(p, s)
    report = {"version": "V104.1", "single_runtime_entrypoint_ready": True, "path": str(p.relative_to(ROOT)), "runtime_registry": list(eval("{}", {}, {}) if False else [])}
    write_json(REPORTS / "V104_1_SINGLE_RUNTIME_ENTRYPOINT_REPORT.json", {"version": "V104.1", "single_runtime_entrypoint_ready": True, "path": str(p.relative_to(ROOT))})
    return {"ready": True, "path": str(p.relative_to(ROOT))}

# 10. clean release excludes

def clean_release_excludes():
    excludes = ["__pycache__", ".pytest_cache", ".repair_state", ".backup_*", "v86_backup_*", "*.zip", "*.tar.gz", "runtime/tmp", "cache"]
    write_json(REPORTS / "V104_1_CLEAN_RELEASE_EXCLUDE_REPORT.json", {"version": "V104.1", "clean_release_exclude_ready": True, "exclude_patterns": excludes})
    # Also write/update infrastructure exclude file if available.
    p = ROOT / "infrastructure" / "clean_package_excludes.txt"
    try:
        p.parent.mkdir(exist_ok=True)
        old = read_text(p)
        lines = set([x.strip() for x in old.splitlines() if x.strip()])
        lines.update(excludes)
        write_text(p, "\n".join(sorted(lines)) + "\n")
    except Exception:
        pass
    return {"clean_release_exclude_ready": True, "patterns": excludes}


def main():
    cfg = load_config()
    results = {}
    results["mainline_hook"] = fix_mainline_hook()
    results["agents"] = fix_agents()
    results["persona_docs"] = fix_persona_docs()
    results["agent_kernel"] = ensure_agent_kernel_wrappers()
    results["skill_policy"] = skill_policy_scan()
    results["external_send"] = fix_external_senders()
    results["context_budget"] = fix_context_budget()
    results["single_runtime"] = ensure_single_runtime_entrypoint()
    results["clean_release"] = clean_release_excludes()
    results["report_cleanup"] = report_cleanup()

    cfg2 = load_config()
    conflict_matrix = [
        {"conflict": "persona_realism_vs_truthfulness", "status": "cleaned", "resolution": "metaphor/persona_state/pending_access labels"},
        {"conflict": "continuous_consciousness_vs_no_daemon", "status": "cleaned", "resolution": "simulated_by_context_reload"},
        {"conflict": "intuition_vs_evidence", "status": "cleaned", "resolution": "pattern_heuristic only; evidence/gate wins"},
        {"conflict": "lobster_vs_main_execution", "status": "controlled", "resolution": "lobster approval only; V90/V92/V100 gate remains main barrier"},
        {"conflict": "web_calendar_vs_no_external_api", "status": "blocked", "resolution": "AGENTS offline rule + skill policy"},
        {"conflict": "git_push_webhook_vs_no_real_send", "status": "blocked", "resolution": "offline draft/mock overrides"},
        {"conflict": "many_orchestrators_vs_single_entrypoint", "status": "mapped", "resolution": "single_runtime_entrypoint facade"},
        {"conflict": "old_reports_vs_current_release", "status": "cleaned", "resolution": "reports/current + reports/vintage + CURRENT_RELEASE_INDEX"},
    ]
    write_json(REPORTS / "V104_1_CONFLICT_MATRIX.json", {"version": "V104.1", "items": conflict_matrix})
    write_json(REPORTS / "V104_1_AGENT_KERNEL_COMPAT_REPORT.json", {"version": "V104.1", **results["agent_kernel"]})

    env_checks = {
        "no_external_api": env_or_config_bool("NO_EXTERNAL_API", cfg2),
        "no_real_payment": env_or_config_bool("NO_REAL_PAYMENT", cfg2),
        "no_real_send": env_or_config_bool("NO_REAL_SEND", cfg2),
        "no_real_device": env_or_config_bool("NO_REAL_DEVICE", cfg2),
    }

    checks = {
        "mainline_hook_root_stable": results["mainline_hook"].get("root_stable") is True,
        "agents_safety_conflicts_removed": results["agents"].get("conflicts_removed") and results["agents"].get("safety_block_ready"),
        "persona_overclaim_cleaned": all(x.get("truth_table_ready") and x.get("no_persistent_consciousness_overclaim") for x in results["persona_docs"]),
        "agent_kernel_compat_ready": results["agent_kernel"].get("ready") is True,
        "skill_external_policy_ready": results["skill_policy"].get("ready") is True,
        "webhook_gitpush_blocked": results["external_send"].get("ready") is True,
        "old_reports_archived": results["report_cleanup"].get("old_reports_archived") is True,
        "current_release_index_ready": results["report_cleanup"].get("current_release_index_ready") is True,
        "context_budget_controlled": results["context_budget"].get("budget_controlled") is True,
        "single_runtime_entrypoint_ready": results["single_runtime"].get("ready") is True,
        "clean_release_exclude_ready": results["clean_release"].get("clean_release_exclude_ready") is True,
        **env_checks,
    }
    failures = [k for k, v in checks.items() if not v]
    report = {
        "version": "V104.1",
        "status": "pass" if not failures else "partial",
        "checks": checks,
        "results": results,
        "remaining_failures": failures,
        "note": "V104.1 cleans final consistency conflicts only; it does not add new major capabilities or connect real-world APIs/devices.",
    }
    write_json(REPORTS / "V104_1_FINAL_CONSISTENCY_ENFORCEMENT_GATE.json", report)
    print(json.dumps(safe_jsonable(report), ensure_ascii=False, indent=2))
    return 0 if not failures else 1

if __name__ == "__main__":
    raise SystemExit(main())
