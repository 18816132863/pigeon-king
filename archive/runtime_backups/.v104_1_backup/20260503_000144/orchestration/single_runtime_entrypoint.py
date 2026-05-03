"""V104 Single Runtime Entrypoint.
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
