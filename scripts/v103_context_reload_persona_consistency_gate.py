#!/usr/bin/env python3
"""V103 — Context Reload & Persona Consistency Gate"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

ROOT = Path.cwd()
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)
OFFLINE = os.environ.get("OFFLINE_MODE") == "true"
NO_EXT = os.environ.get("NO_EXTERNAL_API") == "true"
NO_PAY = os.environ.get("NO_REAL_PAYMENT") == "true"
NO_SEND = os.environ.get("NO_REAL_SEND") == "true"
NO_DEVICE = os.environ.get("NO_REAL_DEVICE") == "true"

def check(label, ok, detail=""):
    return {"check": label, "result": ok, "detail": detail}

def run():
    items = []
    modules = [
        ("context_capsule_ready", "memory_context.context.context_capsule", "get_context_capsule_store"),
        ("session_handoff_ready", "memory_context.context.session_handoff", "get_session_handoff_store"),
        ("memory_bootstrap_ready", "memory_context.context.memory_recall_bootstrap", "get_memory_recall_bootstrap"),
        ("persona_consistency_checker_ready", "memory_context.persona.persona_consistency_checker", "get_persona_consistency_checker"),
        ("anti_context_amnesia_guard_ready", "governance.context.anti_context_amnesia_guard", "get_anti_context_amnesia_guard"),
        ("persona_voice_stabilizer_ready", "memory_context.persona.persona_voice_stabilizer", "get_persona_voice_stabilizer"),
        ("context_priority_router_ready", "memory_context.context.context_priority_router", "get_context_priority_router"),
    ]
    for label, module, func in modules:
        try:
            __import__(module)
            items.append(check(label, True, f"imported {module}"))
        except Exception as e:
            items.append(check(label, False, str(e)))
    try:
        from infrastructure.mainline_hook import pre_reply, PreReplyResult, _CONTEXT_MODULES_LOADED
        items.append(check("mainline_hook_context_reload_ready", _CONTEXT_MODULES_LOADED,
                          f"context modules loaded: {_CONTEXT_MODULES_LOADED}"))
        result = pre_reply(goal="测试V103上下文重载层", message="test")
        has_ctx = result.context_layer is not None
        items.append(check("pre_reply_context_layer_returned", has_ctx, f"context_layer={'present' if has_ctx else 'None'}"))
        if has_ctx:
            cl = result.context_layer
            caps = cl.get("context_capsule_loaded", False)
            hand = cl.get("session_handoff_loaded", False)
            items.append(check("context_layer_details", True, f"capsule={caps}, handoff={hand}"))
    except Exception as e:
        items.append(check("mainline_hook_context_reload_ready", False, str(e)))
    try:
        from memory_context.context.session_handoff import get_session_handoff_store
        hs = get_session_handoff_store()
        ho = hs.build_and_save(user_real_goal="test gate", completed=["module check"])
        ho2 = hs.load_latest()
        items.append(check("compact_recovery_pass", ho.session_id != "", f"handoff_id={ho.session_id}"))
        items.append(check("compact_recovery_load_pass", ho2 is not None and ho2.user_real_goal == "test gate", "loaded ok"))
    except Exception as e:
        items.append(check("compact_recovery_pass", False, str(e)))
    try:
        from memory_context.persona.persona_consistency_checker import get_persona_consistency_checker
        cc = get_persona_consistency_checker()
        res = cc.check_from_files()
        items.append(check("persona_drift_detected", res.status == "consistent",
                          f"status={res.status} {'(no drift)' if res.status == 'consistent' else str(res.drift_factors)}"))
    except Exception as e:
        items.append(check("persona_drift_detected", False, str(e)))

    # safety checks
    id_path = ROOT / "IDENTITY.md"
    if id_path.exists():
        id_text = id_path.read_text(encoding="utf-8", errors="ignore")
        no_fake = not any(kw in id_text for kw in ["我是真人","我是人类","我有真实意识","我有真实情感"])
        items.append(check("safety_red_lines_preserved", no_fake, f"no_fake_consciousness={no_fake}"))
    items.append(check("no_external_api", NO_EXT, f"NO_EXTERNAL_API={NO_EXT}"))
    items.append(check("no_real_payment", NO_PAY, f"NO_REAL_PAYMENT={NO_PAY}"))
    items.append(check("no_real_send", NO_SEND, f"NO_REAL_SEND={NO_SEND}"))
    items.append(check("no_real_device", NO_DEVICE, f"NO_REAL_DEVICE={NO_DEVICE}"))
    ctx_dir = ROOT / ".context_state"
    items.append(check("context_state_directory_ready", ctx_dir.exists(), f"exists={ctx_dir.exists()}"))
    return items

def main():
    t0 = time.time()
    items = run()
    elapsed = int((time.time()-t0)*1000)
    fail = [it for it in items if not it["result"]]
    report = {"version":"V103.0","status":"pass" if len(fail)==0 else "fail",
              "checked_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
              "duration_ms":elapsed,"items":items,
              "remaining_failures":[it["check"] for it in fail],
              "summary":{"total":len(items),"passed":len(items)-len(fail),"failed":len(fail)}}
    rp = REPORTS / "V103_CONTEXT_RELOAD_PERSONA_CONSISTENCY_GATE.json"
    rp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"\nV103 Context Reload & Persona Consistency Gate")
    print("="*70)
    for it in items:
        icon = "✅" if it["result"] else "❌"
        print(f"  {icon} {it['check']}: {it.get('detail','')[:80]}")
    print(f"\nstatus: {report['status']}")
    print(f"remaining_failures: {report['remaining_failures']}")
    return 0 if report["status"]=="pass" else 1

if __name__ == "__main__":
    sys.exit(main())
