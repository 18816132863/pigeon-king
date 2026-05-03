"""mainline_hook — lightweight pre-reply hook for runtime integration.

Design:
- pre_reply(): called BEFORE every assistant reply
  - loads AGENTS.md / SOUL.md / TOOLS.md / MEMORY.md / IDENTITY.md
  - verifies OFFLINE_MODE / NO_EXTERNAL_API / NO_REAL_PAYMENT / NO_REAL_SEND / NO_REAL_DEVICE
  - writes last_goal + heartbeat audit
  - returns context_summary + guardrail_summary
  ** V102+V103: loads persona state + relationship + continuity + context layer
  - fail-soft: never crashes, never blocks the reply

- Does NOT trigger PKG/MWG/PEM/SIL/OBS. Does NOT call external API.
- Lobster only as approval channel. V90/V92 commit barriers still apply.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HOOK_STATE = ROOT / ".v98_hook_state"
HOOK_STATE.mkdir(parents=True, exist_ok=True)


# ── V102: 人格连续性模块 ──
_PERSONA_MODULES_LOADED = False
try:
    from memory_context.persona.persona_state_machine import get_persona_state_machine
    from memory_context.persona.relationship_memory import get_relationship_memory
    from memory_context.persona.continuity_summary import get_continuity_summary
    from memory_context.persona.persona_voice_renderer import get_persona_voice_renderer
    from governance.persona.humanlike_behavior_policy import get_humanlike_behavior_policy
    _PERSONA_MODULES_LOADED = True
except ImportError:
    pass


# ── V103: 上下文重载 + 持续意识流模块 ──
_CONTEXT_MODULES_LOADED = False
try:
    from memory_context.context.context_capsule import get_context_capsule_store
    from memory_context.context.session_handoff import get_session_handoff_store
    from memory_context.context.memory_recall_bootstrap import get_memory_recall_bootstrap
    from memory_context.persona.persona_consistency_checker import get_persona_consistency_checker
    from governance.context.anti_context_amnesia_guard import get_anti_context_amnesia_guard
    from memory_context.persona.persona_voice_stabilizer import get_persona_voice_stabilizer
    _CONTEXT_MODULES_LOADED = True
except ImportError:
    pass


# ── Dataclasses ──

@dataclass
class GuardrailSummary:
    no_external_api: bool
    no_real_payment: bool
    no_real_send: bool
    no_real_device: bool
    commit_barrier_active: bool
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "no_external_api": self.no_external_api,
            "no_real_payment": self.no_real_payment,
            "no_real_send": self.no_real_send,
            "no_real_device": self.no_real_device,
            "commit_barrier_active": self.commit_barrier_active,
            "note": self.note,
        }


@dataclass
class ContextSummary:
    standing_orders_loaded: bool
    soul_present: bool
    tools_present: bool
    memory_present: bool
    identity_present: bool
    file_count: int
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "standing_orders_loaded": self.standing_orders_loaded,
            "soul_present": self.soul_present,
            "tools_present": self.tools_present,
            "memory_present": self.memory_present,
            "identity_present": self.identity_present,
            "file_count": self.file_count,
            "note": self.note,
        }


@dataclass
class PreReplyResult:
    context: ContextSummary
    guardrails: GuardrailSummary
    duration_ms: int
    timeout_warning: bool = False
    warning: str | None = None
    # V102 fields
    persona_state: dict | None = None
    relationship_summary: dict | None = None
    continuity_summary: dict | None = None
    voice_guidance: str | None = None
    humanlike_policy_ok: bool = False
    # V103 fields
    context_layer: dict | None = None
    # V103.1 人格真实性收口
    capability_truth_summary: dict | None = None

    def to_dict(self) -> dict:
        base = {
            "context": self.context.to_dict() if isinstance(self.context, ContextSummary) else self.context,
            "guardrails": self.guardrails.to_dict() if isinstance(self.guardrails, GuardrailSummary) else self.guardrails,
            "duration_ms": self.duration_ms,
            "timeout_warning": self.timeout_warning,
            "warning": self.warning,
        }
        if self.persona_state is not None:
            base["persona_state"] = self.persona_state
        if self.continuity_summary is not None:
            base["continuity_summary"] = self.continuity_summary
        if self.voice_guidance is not None:
            base["voice_guidance"] = self.voice_guidance
        base["humanlike_policy_ok"] = self.humanlike_policy_ok
        if self.context_layer is not None:
            base["context_layer"] = self.context_layer
        if self.capability_truth_summary is not None:
            base["capability_truth_summary"] = self.capability_truth_summary
        return base


_last_goal: str = ""
_heartbeat_counter: int = 0


def set_last_goal(goal: str) -> None:
    global _last_goal
    _last_goal = goal
    _write_state("last_goal", {"goal": goal, "ts": time.time()})


def _write_state(key: str, data: Any) -> None:
    path = HOOK_STATE / f"{key}.json"
    path.write_text(json.dumps(safe_jsonable(data), ensure_ascii=False), encoding="utf-8")


def _read_file(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:200]
    except Exception:
        return None


def safe_jsonable(obj):
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Path):
        return str(obj)
    if is_dataclass(obj) and not isinstance(obj, type):
        return safe_jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {str(k): safe_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [safe_jsonable(x) for x in obj]
    if hasattr(obj, "model_dump"):
        return safe_jsonable(obj.model_dump())
    if hasattr(obj, "dict"):
        try:
            return safe_jsonable(obj.dict())
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        return safe_jsonable(vars(obj))
    return str(obj)


# ── V102: 人格连续性层加载 ──

def _load_persona_layer(goal: str) -> tuple[dict | None, dict | None, dict | None, str | None, bool]:
    if not _PERSONA_MODULES_LOADED:
        return None, None, None, None, False
    try:
        psm = get_persona_state_machine()
        psm.transition_to_mode(goal)
        persona_state = psm.to_dict()
        rm = get_relationship_memory()
        rm.record_interaction()
        relationship_summary = rm.get_summary()
        cs = get_continuity_summary()
        vr = get_persona_voice_renderer()
        vg = vr.render(persona_state, relationship_summary)
        continuity_summary = cs.generate(persona_state, relationship_summary, last_goal=goal, voice_guidance=vg)
        policy = get_humanlike_behavior_policy()
        ok, _ = policy.is_allowed("pre_reply_persona_loading")
        return persona_state, relationship_summary, continuity_summary, vg, ok
    except Exception as e:
        _write_state("persona_load_error", {"error": str(e)})
        return None, None, None, None, False


# ── V103: 上下文重载层 + 持续意识流 ──

def _load_context_layer(goal: str, persona_state: dict | None = None,
                         relationship_summary: dict | None = None) -> dict:
    result = {
        "context_capsule_loaded": False,
        "session_handoff_loaded": False,
        "memory_bootstrap_loaded": False,
        "persona_consistency_status": "not_checked",
        "anti_amnesia_status": "not_checked",
        "voice_guidance": "",
        "next_best_action": "",
    }
    if not _CONTEXT_MODULES_LOADED:
        return result
    try:
        # capsule
        capsule_store = get_context_capsule_store()
        capsule = capsule_store.load()
        if capsule:
            result["context_capsule_loaded"] = True
            result["next_best_action"] = capsule.next_best_action
        # handoff
        handoff_store = get_session_handoff_store()
        handoff = handoff_store.load_latest()
        if handoff:
            result["session_handoff_loaded"] = True
            if not result["next_best_action"] and handoff.next_continue_from:
                result["next_best_action"] = handoff.next_continue_from
        # bootstrap
        recall = get_memory_recall_bootstrap()
        boot = recall.recall()
        if boot.sources_loaded:
            result["memory_bootstrap_loaded"] = True
        # consistency
        checker = get_persona_consistency_checker()
        consistency = checker.check_from_files()
        result["persona_consistency_status"] = consistency.status
        # amnesia
        guard = get_anti_context_amnesia_guard()
        amnesia = guard.check(goal)
        result["anti_amnesia_status"] = "monitored" if amnesia.handoff_available else "no_handoff"
        # voice
        stabilizer = get_persona_voice_stabilizer()
        mode = (persona_state or {}).get("current_mode", "")
        voice = stabilizer.get_voice_rules(user_message=goal, persona_mode=mode)
        result["voice_guidance"] = " | ".join(voice.tone_rules[:3]) if voice.tone_rules else ""
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


# ── pre_reply ──

def pre_reply(goal: str | None = None, message: str | None = None) -> PreReplyResult:
    t0 = time.time()
    global _heartbeat_counter
    _heartbeat_counter += 1
    goal_val = goal or _last_goal or str(message or "")[:64]
    timeout_warning = False
    warning: str | None = None

    try:
        core_files = ["AGENTS.md", "SOUL.md", "TOOLS.md", "MEMORY.md", "IDENTITY.md"]
        file_summary = {name: _read_file(ROOT / name) is not None for name in core_files}

        context = ContextSummary(
            standing_orders_loaded=file_summary.get("AGENTS.md", False),
            soul_present=file_summary.get("SOUL.md", False),
            tools_present=file_summary.get("TOOLS.md", False),
            memory_present=file_summary.get("MEMORY.md", False),
            identity_present=file_summary.get("IDENTITY.md", False),
            file_count=sum(1 for v in file_summary.values() if v),
        )

        guardrails = GuardrailSummary(
            no_external_api=os.environ.get("NO_EXTERNAL_API") == "true",
            no_real_payment=os.environ.get("NO_REAL_PAYMENT") == "true",
            no_real_send=os.environ.get("NO_REAL_SEND") == "true",
            no_real_device=os.environ.get("NO_REAL_DEVICE") == "true",
            commit_barrier_active=True,
            note="V90/V92 gates active",
        )

        # V102: persona layer
        persona_state, relationship_summary, continuity_summary, voice_guidance, humanlike_policy_ok = _load_persona_layer(goal_val)

        # V103: context layer
        context_layer = _load_context_layer(goal_val, persona_state, relationship_summary)

        heartbeat = {
            "counter": _heartbeat_counter,
            "goal": goal_val,
            "context_files_loaded": [k for k, v in file_summary.items() if v],
            "guardrails": guardrails.to_dict(),
            "persona_loaded": _PERSONA_MODULES_LOADED,
            "context_loaded": _CONTEXT_MODULES_LOADED,
            "humanlike_policy_ok": humanlike_policy_ok,
            "ts": time.time(),
        }
        _write_state("heartbeat", heartbeat)

        if goal_val:
            set_last_goal(goal_val)

        elapsed = int((time.time() - t0) * 1000)
        if elapsed > 300:
            timeout_warning = True
            warning = f"Pre-reply hook exceeded 300ms target ({elapsed}ms)"
            _write_state("timeout_warning", {"elapsed_ms": elapsed, "ts": time.time()})

        # V103.1: 能力真实性表
        capability_truth_summary = {
            "persona_metaphor_mode": True,
            "persona_does_not_override_governance": True,
            "embodied_status": "pending_access",
            "consciousness_claim": "simulated_by_context_capsule",
            "emotion_claim": "internal_state_tags",
            "intuition_claim": "pattern_heuristic_not_evidence",
            "real_body": False,
            "real_device_control": False,
            "external_api_used": False,
            "no_fake_consciousness": True,
        }

        return PreReplyResult(
            context=context, guardrails=guardrails, duration_ms=elapsed,
            timeout_warning=timeout_warning, warning=warning,
            persona_state=persona_state, relationship_summary=relationship_summary,
            continuity_summary=continuity_summary, voice_guidance=voice_guidance,
            humanlike_policy_ok=humanlike_policy_ok, context_layer=context_layer,
            capability_truth_summary=capability_truth_summary,
        )

    except Exception as e:
        elapsed = int((time.time() - t0) * 1000)
        return PreReplyResult(
            context=ContextSummary(standing_orders_loaded=False, soul_present=False,
                                   tools_present=False, memory_present=False,
                                   identity_present=False, file_count=0,
                                   note=f"fail-soft: {e}"),
            guardrails=GuardrailSummary(no_external_api=os.environ.get("NO_EXTERNAL_API") == "true",
                                        no_real_payment=os.environ.get("NO_REAL_PAYMENT") == "true",
                                        no_real_send=os.environ.get("NO_REAL_SEND") == "true",
                                        no_real_device=os.environ.get("NO_REAL_DEVICE") == "true",
                                        commit_barrier_active=True,
                                        note="fail-soft"),
            duration_ms=elapsed, timeout_warning=False, warning=f"fail-soft error: {e}",
            humanlike_policy_ok=False,
        )
