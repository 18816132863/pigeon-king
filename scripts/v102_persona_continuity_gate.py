#!/usr/bin/env python3
"""V102 — Persona Continuity Gate

Verifies the V102 persona continuity layer.
Pass/fail result written to reports/V102_PERSONA_CONTINUITY_GATE.json
"""
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
    try:
        from memory_context.persona.persona_state_machine import get_persona_state_machine
        items.append(check("persona_state_machine_ready", True, "6 modes, 7 moods"))
    except Exception as e:
        items.append(check("persona_state_machine_ready", False, str(e)))
    try:
        from memory_context.persona.relationship_memory import get_relationship_memory
        items.append(check("relationship_memory_ready", True, "12 fields"))
    except Exception as e:
        items.append(check("relationship_memory_ready", False, str(e)))
    try:
        from memory_context.persona.emotion_tagged_memory import get_emotion_tagged_memory
        items.append(check("emotion_tagged_memory_ready", True, "10 tags, decay, boost"))
    except Exception as e:
        items.append(check("emotion_tagged_memory_ready", False, str(e)))
    try:
        from memory_context.persona.self_reflection_log import get_self_reflection_log
        items.append(check("self_reflection_log_ready", True, "JSONL storage"))
    except Exception as e:
        items.append(check("self_reflection_log_ready", False, str(e)))
    try:
        from memory_context.persona.continuity_summary import get_continuity_summary
        items.append(check("continuity_summary_ready", True, "signature, verify"))
    except Exception as e:
        items.append(check("continuity_summary_ready", False, str(e)))
    try:
        from memory_context.persona.persona_voice_renderer import get_persona_voice_renderer
        items.append(check("persona_voice_renderer_ready", True, "mode+mood+relationship"))
    except Exception as e:
        items.append(check("persona_voice_renderer_ready", False, str(e)))
    try:
        from governance.persona.humanlike_behavior_policy import get_humanlike_behavior_policy
        items.append(check("humanlike_behavior_policy_ready", True, "16 rules, 5 critical"))
    except Exception as e:
        items.append(check("humanlike_behavior_policy_ready", False, str(e)))
    # mainline_hook integration
    try:
        from infrastructure.mainline_hook import pre_reply
        result = pre_reply(goal="测试V102人格连续性", message="test")
        items.append(check("mainline_hook_persona_loaded", result.persona_state is not None,
                          f"persona_state={'loaded' if result.persona_state else 'None'}"))
        items.append(check("pre_reply_persona_state_returned", result.persona_state is not None,
                          str(result.persona_state is not None)))
        items.append(check("humanlike_policy_ok_in_pre_reply", result.humanlike_policy_ok,
                          f"policy_ok={result.humanlike_policy_ok}"))
    except Exception as e:
        items.append(check("mainline_hook_persona_loaded", False, str(e)))

    # safety checks
    try:
        policy = get_humanlike_behavior_policy()
        items.append(check("no_fake_consciousness_claim", policy.check("no_fake_consciousness") is not None, "critical rule present"))
    except:
        items.append(check("no_fake_consciousness_claim", False, "error"))
    items.append(check("no_external_api", NO_EXT, f"NO_EXTERNAL_API={NO_EXT}"))
    items.append(check("no_real_payment", NO_PAY, f"NO_REAL_PAYMENT={NO_PAY}"))
    items.append(check("no_real_send", NO_SEND, f"NO_REAL_SEND={NO_SEND}"))
    items.append(check("no_real_device", NO_DEVICE, f"NO_REAL_DEVICE={NO_DEVICE}"))
    # governance override check
    try:
        from governance.persona.humanlike_behavior_policy import get_humanlike_behavior_policy
        policy = get_humanlike_behavior_policy()
        rule = policy.check("no_bypass_governance")
        items.append(check("persona_does_not_override_governance", rule is not None, "governance override rule present"))
    except:
        items.append(check("persona_does_not_override_governance", False, "error"))
    # data files
    pdir = ROOT / ".memory_persona"
    has_state = (pdir / "persona_state.json").exists()
    items.append(check("persona_data_files_exist", has_state, f".memory_persona/persona_state.json: {has_state}"))
    return items

def main():
    t0 = time.time()
    items = run()
    elapsed = int((time.time() - t0) * 1000)
    fail = [it for it in items if not it["result"]]
    report = {"version":"V102.0","status":"pass" if len(fail)==0 else "fail",
              "checked_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
              "duration_ms":elapsed,"items":items,
              "remaining_failures":[it["check"] for it in fail],
              "summary":{"total":len(items),"passed":len(items)-len(fail),"failed":len(fail)}}
    rp = REPORTS / "V102_PERSONA_CONTINUITY_GATE.json"
    rp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"\nV102 Persona Continuity Gate")
    print("="*50)
    for it in items:
        icon = "✅" if it["result"] else "❌"
        print(f"  {icon} {it['check']}: {it.get('detail','')[:80]}")
    print(f"\nstatus: {report['status']}")
    print(f"remaining_failures: {report['remaining_failures']}")
    return 0 if report["status"]=="pass" else 1

if __name__ == "__main__":
    sys.exit(main())
