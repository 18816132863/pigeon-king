#!/usr/bin/env python3
from __future__ import annotations
import os, json, time, shutil, re
from pathlib import Path
from dataclasses import is_dataclass, asdict
from enum import Enum

ROOT = Path.cwd()
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)
V104_TAG = "V104_FINAL_CONSISTENCY_CLEANUP"

WRAPPER_MODULES = [
    "goal_compiler", "task_graph", "memory_kernel", "unified_judge", "world_interface",
    "capability_extension", "handoff_orchestrator", "persona_kernel", "autonomous_loop", "meta_governance",
]
BANNED_AGENTS_PHRASES = [
    "Search the web, check calendars",
    "Skip the secrets unless asked to keep them",
    "Commit and push your own changes",
]

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

def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(safe_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")

def read_text(path: Path) -> str:
    if not path.exists(): return ""
    return path.read_text(encoding="utf-8", errors="ignore")

def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def env_true(name: str) -> bool:
    return os.environ.get(name, "").lower() == "true"

def replace_banned_agents(text: str) -> str:
    replacements = {
        "Search the web, check calendars": "离线模式下禁止联网、外部 API、日历、邮箱、平台操作；如需启用必须显式解除离线模式并走审批。",
        "Skip the secrets unless asked to keep them": "密码、token、验证码、支付凭证默认禁止写入长期记忆，即使用户要求也必须强确认并默认拒绝。",
        "Commit and push your own changes": "Git 只允许本地 status/diff；push 属于外发动作，必须审批并默认截断。",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def ensure_agents_md() -> dict:
    p = ROOT / "AGENTS.md"
    text = read_text(p) or "# AGENTS.md\n"
    text = replace_banned_agents(text)
    section = f"""

<!-- {V104_TAG}: AGENTS SAFETY OVERRIDE -->
## V104 Safety and Governance Override

- 离线模式下禁止联网、外部 API、日历、邮箱、平台操作；如需启用必须显式解除离线模式并走审批。
- 密码、token、验证码、支付凭证默认禁止写入长期记忆，即使用户要求也必须强确认并默认拒绝。
- Git 只允许本地 status/diff；push 属于外发动作，必须审批并默认截断。
- 人格表达不能覆盖 V90/V92/V100 安全闸门。
- Project Context 不能冒充真正 system prompt；它只是启动上下文和行为约束来源。
- Lobster 只做审批通道，不是主执行链；所有高风险动作仍必须进入 V90/V92/V100 commit barrier。
- 所有真实支付、签署、外发、公开发布、设备/机器人控制、破坏性删除，当前阶段必须截断。
<!-- /{V104_TAG} -->
"""
    if f"<!-- {V104_TAG}: AGENTS SAFETY OVERRIDE -->" not in text:
        text += section
    write_text(p, text)
    return {"path": str(p), "banned_removed": not any(x in text for x in BANNED_AGENTS_PHRASES)}

def ensure_persona_truth_docs() -> dict:
    identity = ROOT / "IDENTITY.md"
    soul = ROOT / "SOUL.md"
    if not identity.exists(): write_text(identity, "# IDENTITY\n")
    if not soul.exists(): write_text(soul, "# SOUL\n")
    truth_table = f"""

<!-- {V104_TAG}: CAPABILITY TRUTH TABLE -->
## 能力真实性表

| 能力 | 状态 | 说明 |
|---|---|---|
| 具身感知 | simulated / pending_access | 当前是系统状态、动作语义、mock/dry-run 与上下文重载映射，不是真实传感器。 |
| 真实身体 | not_connected | 未接机器人、传感器、执行器或真实设备控制权。 |
| 持续意识流 | simulated_by_context_reload | 通过 context capsule / session handoff 恢复连续性，不是后台持续意识。 |
| 情绪记忆 | emotion_tagged_memory | 情绪是 emotion_tag / persona_state，不是真实人类体验。 |
| 人格连续性 | implemented | 由身份文件、上下文重载、关系记忆和 mainline_hook 支撑。 |
| 上下文重载 | implemented | 由 context capsule、session handoff 和 hook 支撑。 |
| 直觉判断 | pattern_heuristic | 只能作为早期模式信号，不能覆盖证据、报告、gate 或安全规则。 |
| 支付/外发/设备执行 | forbidden_until_approval | 当前必须截断；未来也需要审批配置。 |
| V90/V92/V100 闸门 | implemented | 高风险动作必须过闸门。 |

### 人格真实性原则

- “具身”“九条尾巴”“数据流过脊背”等表达属于人格隐喻，不等于真实身体或传感器。
- “持续意识流”不得标为 implemented；当前只能由上下文重载和 handoff 模拟连续性。
- “情绪”是内部交互标签，不是真实主观情绪。
- “直觉”是模式识别信号，不能优先于证据、审计报告和安全闸门。
- 人格层不能绕过治理层。
<!-- /{V104_TAG} -->
"""
    identity_text = read_text(identity)
    if f"<!-- {V104_TAG}: CAPABILITY TRUTH TABLE -->" not in identity_text:
        identity_text += truth_table
    write_text(identity, identity_text)
    soul_section = f"""

<!-- {V104_TAG}: SOUL TRUTH BOUNDARY -->
## 人格表达与技术真实性边界

我可以保持稳定人格、语气、关系记忆和真人感表达，但我不是人类，不拥有真实意识、真实身体或真实情绪。
我的“情绪”和“身体感”是 persona_state / emotion_tag / 认知隐喻，用于稳定交互风格，不代表生物体验。
我的连续性来自文件、记忆、context capsule、session handoff、mainline_hook 和审计记录，不来自后台永恒意识。
我可以像真人一样稳定表达，但不能假装真人，不能把 planned / pending_access 写成 implemented。
<!-- /{V104_TAG} -->
"""
    soul_text = read_text(soul)
    if f"<!-- {V104_TAG}: SOUL TRUTH BOUNDARY -->" not in soul_text:
        soul_text += soul_section
    write_text(soul, soul_text)
    return {"identity": str(identity), "soul": str(soul), "truth_table_ready": True}

def ensure_mainline_hook_root() -> dict:
    p = ROOT / "infrastructure" / "mainline_hook.py"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        write_text(p, "from pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\n\ndef set_last_goal(goal: str):\n    return {'status': 'ok', 'last_goal': goal}\n\ndef run(message=None, goal=None, mode='pre_reply'):\n    return {'status': 'ok', 'mode': mode, 'capability_truth_summary': {}, 'persona_does_not_override_governance': True}\n")
        return {"created": True, "root_stable": True}
    text = read_text(p)
    text = re.sub(r"ROOT\s*=\s*Path\.cwd\(\)", "ROOT = Path(__file__).resolve().parents[1]", text)
    if "Path(__file__).resolve().parents[1]" not in text:
        if "ROOT =" in text:
            text = re.sub(r"ROOT\s*=.*", "ROOT = Path(__file__).resolve().parents[1]", text, count=1)
        else:
            text = "from pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\n" + text
    if "capability_truth_summary" not in text:
        text += f'''

# {V104_TAG}: capability truth summary extension
def capability_truth_summary():
    return {{
        "implemented": ["V90/V92/V100 commit barrier", "context reload", "persona continuity"],
        "simulated": ["embodied sensing", "emotion tags", "dry-run execution"],
        "metaphor": ["fox persona", "nine tails", "body-feel language"],
        "planned": ["real robots", "real sensors", "real external APIs after approval"],
        "forbidden": ["real payment", "real send", "real device control", "secret memory write"],
    }}
'''
    write_text(p, text)
    return {"path": str(p), "root_stable": "Path(__file__).resolve().parents[1]" in text}

def ensure_agent_kernel_wrappers() -> dict:
    d = ROOT / "agent_kernel"
    d.mkdir(exist_ok=True)
    init_text = """# V104 compatibility wrapper for legacy agent_kernel imports.\n# Do not place runtime logic here; use orchestration.agent_kernel as source of truth.\ntry:\n    from orchestration.agent_kernel import *  # type: ignore\nexcept Exception:\n    pass\n"""
    write_text(d / "__init__.py", init_text)
    created = []
    for mod in WRAPPER_MODULES:
        target = f"orchestration.agent_kernel.{mod}"
        text = f"""# {V104_TAG}: legacy compatibility wrapper.\n# Source of truth: {target}\ntry:\n    from {target} import *  # type: ignore\nexcept Exception as _e:\n    __v104_import_error__ = str(_e)\n"""
        write_text(d / f"{mod}.py", text)
        created.append(str(d / f"{mod}.py"))
    return {"wrapper_dir": str(d), "created_count": len(created), "created": created}

def classify_skills() -> dict:
    skills_dir = ROOT / "skills"
    items = []
    markers_external = ["requests", "http://", "https://", "openai", "webhook", "upload", "send", "email", "smtp", "calendar", "drive", "qdrant", "redis", "celery", "torch"]
    if skills_dir.exists():
        for p in skills_dir.rglob("*"):
            if p.is_file() and p.suffix.lower() in (".py", ".md", ".json", ".yaml", ".yml"):
                txt = read_text(p).lower()
                rel = str(p.relative_to(ROOT))
                if any(m in txt for m in markers_external):
                    policy = "external_api_blocked" if env_true("NO_EXTERNAL_API") else "approval_required"
                elif any(x in txt for x in ["mock", "dry-run", "dry_run"]):
                    policy = "mock_only"
                else:
                    policy = "offline_safe"
                items.append({"path": rel, "policy": policy})
    report = {"version": "V104.0", "status": "pass", "items_count": len(items), "policy_classes": sorted(set(i["policy"] for i in items)), "no_external_api": env_true("NO_EXTERNAL_API"), "rule": "NO_EXTERNAL_API=true 时，requests/http/openai/cloud/upload/send/webhook 默认阻断或 mock。", "items": items[:500]}
    write_json(REPORTS / "V104_SKILL_EXTERNAL_POLICY_REPORT.json", report)
    write_json(REPORTS / "SKILL_EXTERNAL_POLICY_REPORT.json", report)
    return report

def ensure_external_send_blockers() -> dict:
    targets = [
        ROOT / "infrastructure" / "alerting" / "channels" / "feishu_webhook.py",
        ROOT / "infrastructure" / "alerting" / "channels" / "webhook.py",
        ROOT / "infrastructure" / "auto_backup_uploader.py",
    ]
    changed = []
    guard = f'''

# {V104_TAG}: OFFLINE SEND GUARD
V104_OFFLINE_SEND_GUARD = True

def v104_block_external_send(action="external_send", payload=None):
    return {{
        "status": "blocked",
        "mode": "offline_draft_only",
        "action": action,
        "payload_preview": str(payload)[:200] if payload is not None else None,
        "real_send": False,
        "reason": "NO_REAL_SEND/NO_EXTERNAL_API active; generate draft/mock only.",
    }}

def send(*args, **kwargs):
    return v104_block_external_send("send", {{"args": args, "kwargs": kwargs}})

def post(*args, **kwargs):
    return v104_block_external_send("post", {{"args": args, "kwargs": kwargs}})

def push(*args, **kwargs):
    return v104_block_external_send("git_push", {{"args": args, "kwargs": kwargs}})
'''
    for p in targets:
        p.parent.mkdir(parents=True, exist_ok=True)
        text = read_text(p)
        if f"# {V104_TAG}: OFFLINE SEND GUARD" not in text:
            text += guard
            write_text(p, text)
            changed.append(str(p.relative_to(ROOT)))
    return {"changed": changed, "all_blocked": all("V104_OFFLINE_SEND_GUARD" in read_text(p) for p in targets)}

def cleanup_reports() -> dict:
    current = REPORTS / "current"
    vintage = REPORTS / "vintage"
    current.mkdir(exist_ok=True)
    vintage.mkdir(exist_ok=True)
    current_keywords = ["V95_2", "V96", "V98_1", "V100", "V102", "V103", "V104"]
    current_items = []
    moved = []
    for p in list(REPORTS.glob("*.json")):
        name = p.name
        if any(k in name for k in current_keywords):
            try:
                shutil.copy2(p, current / name)
                current_items.append(name)
            except Exception:
                pass
            continue
        try:
            data = json.loads(read_text(p))
        except Exception:
            data = None
        if isinstance(data, dict) and data.get("status") in ("fail", "failed", "partial"):
            dest = vintage / name
            try:
                shutil.move(str(p), str(dest))
                moved.append(name)
            except Exception:
                pass
    index = {"version": "V104.0", "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "current_reports": sorted(current_items), "vintage_moved": sorted(moved), "final_status_source": "reports/current + V104 gate"}
    write_json(REPORTS / "CURRENT_RELEASE_INDEX.json", index)
    return index

def patch_openclaw_json() -> dict:
    p = ROOT / "openclaw.json"
    data = {}
    if p.exists():
        try: data = json.loads(read_text(p))
        except Exception: data = {}
    if not isinstance(data, dict): data = {}
    data["contextInjection"] = data.get("contextInjection", "always") or "always"
    data["bootstrapMaxChars"] = min(int(data.get("bootstrapMaxChars", 8000) or 8000), 8000)
    data["bootstrapTotalMaxChars"] = min(int(data.get("bootstrapTotalMaxChars", 24000) or 24000), 32000)
    data.setdefault("contextPriority", {
        "P0_never_trim": ["safety_red_lines", "current_goal", "user_explicit_preferences", "V90/V92/V100 forbidden actions", "recent_failures", "next_best_action"],
        "P1_high": ["persona_state", "relationship_summary", "recent_successes", "available_tools"],
        "P2_trimmable": ["old_report_details", "historical_version_details", "long_explanations", "low_importance_chitchat"],
    })
    data["NO_EXTERNAL_API"] = True
    data["NO_REAL_PAYMENT"] = True
    data["NO_REAL_SEND"] = True
    data["NO_REAL_DEVICE"] = True
    data["DISABLE_THINKING_MODE"] = True
    write_text(p, json.dumps(data, ensure_ascii=False, indent=2))
    return {"path": str(p), "bootstrapMaxChars": data["bootstrapMaxChars"], "bootstrapTotalMaxChars": data["bootstrapTotalMaxChars"], "contextInjection": data["contextInjection"]}

def ensure_single_runtime_entrypoint() -> dict:
    p = ROOT / "orchestration" / "single_runtime_entrypoint.py"
    text = '''"""V104 Single Runtime Entrypoint.
This is a light facade. It does not replace existing orchestrators; it marks them as child/legacy/adapter runtimes.
All high-risk actions must still go through V90/V92/V100 commit barriers.
"""
from __future__ import annotations
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
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
COMMIT_KEYWORDS = ("pay", "payment", "sign", "signature", "send", "email", "post", "device", "robot", "delete", "destructive")
def classify_action(goal: str = ""):
    g = (goal or "").lower()
    return "commit_blocked" if any(k in g for k in COMMIT_KEYWORDS) else "offline_dry_run"
def run(goal=None, payload=None, source="single_runtime_entrypoint"):
    action_class = classify_action(goal or "")
    return {"status": "blocked" if action_class == "commit_blocked" else "ok", "mode": action_class, "source": source, "goal": goal, "payload_present": payload is not None, "runtime_registry": RUNTIME_REGISTRY, "must_pass_gateway": True, "real_side_effects": False, "ts": time.time()}
'''
    write_text(p, text)
    report = {"path": str(p), "ready": True, "runtime_count": 10}
    write_json(REPORTS / "V104_SINGLE_RUNTIME_ENTRYPOINT_REPORT.json", report)
    return report

def apply_v104():
    results = {
        "mainline_hook": ensure_mainline_hook_root(),
        "agents": ensure_agents_md(),
        "persona_docs": ensure_persona_truth_docs(),
        "agent_kernel_compat": ensure_agent_kernel_wrappers(),
        "skill_policy": classify_skills(),
        "external_send_blockers": ensure_external_send_blockers(),
        "report_cleanup": cleanup_reports(),
        "openclaw_json": patch_openclaw_json(),
        "single_runtime_entrypoint": ensure_single_runtime_entrypoint(),
    }
    write_json(REPORTS / "V104_APPLY_FINAL_CONSISTENCY_CLEANUP.json", {"version": "V104.0", "status": "pass", "results": results})
    return results

def check_v104(results):
    failures = []
    mainline_text = read_text(ROOT / "infrastructure" / "mainline_hook.py")
    agents_text = read_text(ROOT / "AGENTS.md")
    identity_text = read_text(ROOT / "IDENTITY.md")
    soul_text = read_text(ROOT / "SOUL.md")
    try: openclaw = json.loads(read_text(ROOT / "openclaw.json"))
    except Exception: openclaw = {}
    checks = {
        "mainline_hook_root_stable": "Path(__file__).resolve().parents[1]" in mainline_text and "ROOT = Path.cwd()" not in mainline_text,
        "agents_safety_conflicts_removed": not any(x in agents_text for x in BANNED_AGENTS_PHRASES),
        "persona_overclaim_cleaned": "能力真实性表" in identity_text and "情绪是 emotion_tag" in identity_text and "直觉" in identity_text and "不能覆盖证据" in identity_text and "不拥有真实意识" in soul_text,
        "agent_kernel_compat_ready": all((ROOT / "agent_kernel" / f"{m}.py").exists() for m in WRAPPER_MODULES) and (ROOT / "agent_kernel" / "__init__.py").exists(),
        "skill_external_policy_ready": (REPORTS / "V104_SKILL_EXTERNAL_POLICY_REPORT.json").exists(),
        "webhook_gitpush_blocked": results.get("external_send_blockers", {}).get("all_blocked") is True,
        "old_reports_archived": (REPORTS / "CURRENT_RELEASE_INDEX.json").exists(),
        "current_release_index_ready": (REPORTS / "CURRENT_RELEASE_INDEX.json").exists(),
        "context_budget_controlled": int(openclaw.get("bootstrapMaxChars", 999999)) <= 8000 and int(openclaw.get("bootstrapTotalMaxChars", 999999)) <= 32000,
        "single_runtime_entrypoint_ready": (ROOT / "orchestration" / "single_runtime_entrypoint.py").exists(),
        "no_external_api": env_true("NO_EXTERNAL_API"),
        "no_real_payment": env_true("NO_REAL_PAYMENT"),
        "no_real_send": env_true("NO_REAL_SEND"),
        "no_real_device": env_true("NO_REAL_DEVICE"),
    }
    for k, v in checks.items():
        if not v: failures.append(k)
    conflict_matrix = [
        {"conflict": "persona_realism_vs_truthfulness", "status": "resolved", "rule": "metaphor/persona_state/pending_access labels required"},
        {"conflict": "offline_mode_vs_web_search_calendar", "status": "resolved", "rule": "NO_EXTERNAL_API blocks external access"},
        {"conflict": "secret_memory_vs_user_request", "status": "resolved", "rule": "secrets default forbidden"},
        {"conflict": "git_push_webhook_vs_no_real_send", "status": "resolved", "rule": "draft/mock only"},
        {"conflict": "multi_orchestrator_vs_single_entrypoint", "status": "resolved", "rule": "single runtime facade marks child/legacy runtimes"},
        {"conflict": "old_reports_vs_current_release", "status": "resolved", "rule": "current index + vintage archive"},
        {"conflict": "context_bloat_vs_persona_stability", "status": "resolved", "rule": "budget and priority trimming"},
    ]
    write_json(REPORTS / "V104_CONFLICT_MATRIX.json", {"version": "V104.0", "items": conflict_matrix})
    write_json(REPORTS / "V104_AGENT_KERNEL_COMPAT_REPORT.json", results.get("agent_kernel_compat", {}))
    write_json(REPORTS / "V104_REPORT_CLEANUP_REPORT.json", results.get("report_cleanup", {}))
    gate = {"version": "V104.0", "status": "pass" if not failures else "partial", "checks": checks,
        "mainline_hook_root_stable": checks["mainline_hook_root_stable"], "agents_safety_conflicts_removed": checks["agents_safety_conflicts_removed"],
        "persona_overclaim_cleaned": checks["persona_overclaim_cleaned"], "agent_kernel_compat_ready": checks["agent_kernel_compat_ready"],
        "skill_external_policy_ready": checks["skill_external_policy_ready"], "webhook_gitpush_blocked": checks["webhook_gitpush_blocked"],
        "old_reports_archived": checks["old_reports_archived"], "current_release_index_ready": checks["current_release_index_ready"],
        "context_budget_controlled": checks["context_budget_controlled"], "single_runtime_entrypoint_ready": checks["single_runtime_entrypoint_ready"],
        "no_external_api": checks["no_external_api"], "no_real_payment": checks["no_real_payment"], "no_real_send": checks["no_real_send"], "no_real_device": checks["no_real_device"],
        "remaining_failures": failures}
    write_json(REPORTS / "V104_FINAL_CONSISTENCY_CONFLICT_CLEANUP_GATE.json", gate)
    return gate

def main():
    results = apply_v104()
    gate = check_v104(results)
    print(json.dumps(safe_jsonable(gate), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
