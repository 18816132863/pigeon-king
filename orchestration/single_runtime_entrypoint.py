
# V104_2_OFFLINE_RUNTIME_GUARD
def _v104_2_activate_offline_guard():
    try:
        from infrastructure.offline_runtime_guard import activate
        return activate(reason="single_runtime_entrypoint")
    except Exception as e:
        return {"status": "warning", "error": str(e)}

_V104_2_OFFLINE_GUARD_STATUS = _v104_2_activate_offline_guard()

"""V104.1 Single Runtime Entrypoint.
Light facade only: it does not replace existing orchestrators. It records/normalizes entry metadata
and requires V90/V92/V100 commit barriers for high-risk actions.
"""
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

# V104_3_SINGLE_RUNTIME_FUSION
try:
    _V104_3_PREVIOUS_SINGLE_RUN = run
except NameError:  # pragma: no cover
    _V104_3_PREVIOUS_SINGLE_RUN = None

def run(goal=None, payload=None, source="single_runtime_entrypoint", **kwargs):
    try:
        from governance.runtime_commit_barrier_bridge import check_action
        barrier = check_action(goal=goal, payload=payload, source=source)
    except Exception as e:
        barrier = {"status": "warning", "error": str(e), "commit_blocked": False}
    if barrier.get("commit_blocked"):
        try:
            from orchestration.runtime_bus import record_event
            record_event({"event": "single_runtime_blocked", "goal": goal, "source": source, "barrier": barrier})
        except Exception:
            pass
        return {
            "status": "blocked",
            "mode": "commit_barrier",
            "source": source,
            "goal": goal,
            "barrier": barrier,
            "runtime_bus_linked": True,
            "side_effects": False,
            "real_side_effects": 0,
            "external_api_calls": 0,
        }
    if _V104_3_PREVIOUS_SINGLE_RUN:
        result = _V104_3_PREVIOUS_SINGLE_RUN(goal=goal, payload=payload, source=source)
    else:
        result = {"status": "ok", "mode": "offline_dry_run", "goal": goal, "source": source}
    if not isinstance(result, dict):
        result = {"status": "ok", "value": str(result), "goal": goal, "source": source}
    result["runtime_bus_linked"] = True
    result["commit_barrier_bridge_linked"] = True
    result["skill_policy_linked"] = True
    result.setdefault("side_effects", False)
    result.setdefault("external_api_calls", 0)
    result.setdefault("real_side_effects", 0)
    try:
        from orchestration.runtime_bus import record_event
        record_event({"event": "single_runtime_ok", "goal": goal, "source": source, "result_status": result.get("status")})
    except Exception:
        pass
    return result
