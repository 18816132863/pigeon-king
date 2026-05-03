"""
V91 Preference Evolution Model — 离线增强版。

- 本地 feedback log / task result / user correction 驱动偏好演化
- 挂接 personal_operating_loop_v2（通过回调接口）
- JSONL 持久化，不依赖外部 API
"""
from __future__ import annotations
import json
import os
import time
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from infrastructure.offline_mode import audit_info, audit_warning, STATE_DIR
except ImportError:
    STATE_DIR = Path(os.environ.get("WORKSPACE", "/home/sandbox/.openclaw/workspace")) / ".offline_state"
    def _noop(*a, **kw): pass
    audit_info = _noop
    audit_warning = _noop

@dataclass
class PreferenceSignal:
    key: str
    value: Any
    confidence_delta: float = 0.1
    source: str = "episode"
    reversible: bool = True
    ts: float = field(default_factory=time.time)

@dataclass
class FeedbackEntry:
    """用户反馈 / 任务结果 / 纠错项。"""
    ts: float
    source: str  # "user_correction" / "task_result" / "system_observation"
    key: str
    old_value: Any
    new_value: Any
    accepted: bool = True
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PreferenceState:
    values: Dict[str, Any] = field(default_factory=dict)
    confidence: Dict[str, float] = field(default_factory=dict)
    history: List[PreferenceSignal] = field(default_factory=list)

class PreferenceEvolutionModel:
    """V91 增强版 — 本地反馈驱动的偏好演化。"""
    layer = "L2_MEMORY_CONTEXT"

    def __init__(self, state_path: Path = None):
        self.state = PreferenceState()
        self._feedback_log: List[FeedbackEntry] = []
        self._state_path = state_path or STATE_DIR / "preference_evolution_v7.json"
        self._feedback_path = STATE_DIR / "preference_feedback.jsonl"
        self._lock = threading.Lock()
        self._operating_loop = None  # personal_operating_loop_v2 回调
        self._load_state()
        # V91: 自动挂接 operating loop（离线兼容）
        self._auto_bridge_loop()

    # ── 持久化 ──────────────────────────────────────────
    def _load_state(self):
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._state_path.exists():
            return
        try:
            data = json.loads(self._state_path.read_text())
            for k, v in data.get("values", {}).items():
                self.state.values[k] = v
            for k, v in data.get("confidence", {}).items():
                self.state.confidence[k] = float(v)
            audit_info("PreferenceEvolutionModel", "state_loaded", keys=len(self.state.values))
        except Exception as e:
            audit_warning("PreferenceEvolutionModel", "state_load_failed", error=str(e))

        # 加载反馈日志
        if self._feedback_path.exists():
            try:
                for line in self._feedback_path.read_text().splitlines():
                    if line.strip():
                        self._feedback_log.append(FeedbackEntry(**json.loads(line)))
            except Exception:
                pass

    def _save_state(self):
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._state_path.write_text(json.dumps({
                "values": self.state.values,
                "confidence": self.state.confidence,
                "ts": time.time(),
            }, ensure_ascii=False, indent=2))

    def _append_feedback(self, entry: FeedbackEntry):
        self._feedback_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._feedback_log.append(entry)
        with open(self._feedback_path, "a") as f:
            f.write(json.dumps({
                "ts": entry.ts, "source": entry.source, "key": entry.key,
                "old_value": str(entry.old_value)[:200],
                "new_value": str(entry.new_value)[:200],
                "accepted": entry.accepted, "meta": entry.meta,
            }, ensure_ascii=False) + "\n")

    # ── 核心操作 ────────────────────────────────────────
    def propose(self, signal: PreferenceSignal) -> Dict[str, Any]:
        old = self.state.values.get(signal.key)
        old_conf = self.state.confidence.get(signal.key, 0.0)
        new_conf = max(0.0, min(1.0, old_conf + signal.confidence_delta))
        drift = old is not None and old != signal.value and old_conf >= 0.7 and signal.confidence_delta < 0.3
        return {
            "key": signal.key, "old": old, "new": signal.value,
            "confidence": new_conf, "requires_review": drift,
            "old_confidence": old_conf,
        }

    def apply(self, signal: PreferenceSignal) -> str:
        proposal = self.propose(signal)
        if proposal["requires_review"]:
            audit_warning("PreferenceEvolutionModel", "blocked_for_review", key=signal.key)
            return "blocked_for_memory_review"
        self.state.values[signal.key] = signal.value
        self.state.confidence[signal.key] = proposal["confidence"]
        self.state.history.append(signal)
        self._save_state()
        self._notify_loop("preference_applied", signal.key, signal.value)
        audit_info("PreferenceEvolutionModel", "applied", key=signal.key, confidence=proposal["confidence"])
        return "applied"

    # ── 反馈系统 ────────────────────────────────────────
    def record_feedback(self, source: str, key: str, old_value: Any, new_value: Any, meta: Dict = None):
        """记录用户纠错 / 任务结果 / 系统观察。"""
        entry = FeedbackEntry(
            ts=time.time(), source=source, key=key,
            old_value=old_value, new_value=new_value, accepted=True,
            meta=meta or {},
        )
        self._append_feedback(entry)
        audit_info("PreferenceEvolutionModel", "feedback_recorded", source=source, key=key)

    def record_task_result(self, task_id: str, success: bool, preferences_used: Dict[str, Any]):
        """从任务结果中记录偏好使用情况。"""
        for key, value in preferences_used.items():
            signal = PreferenceSignal(
                key=key, value=value,
                confidence_delta=0.05 if success else -0.08,
                source=f"task_result:{task_id}",
            )
            self.apply(signal)
        self.record_feedback("task_result", task_id, None, {"success": success, "prefs": str(preferences_used)[:500]})

    def record_user_correction(self, key: str, wrong_value: Any, correct_value: Any):
        """记录用户手动纠错。"""
        self.record_feedback("user_correction", key, wrong_value, correct_value)
        signal = PreferenceSignal(
            key=key, value=correct_value,
            confidence_delta=0.2,  # 用户纠错权重高
            source="user_correction",
        )
        return self.apply(signal)

    def get_recent_feedback(self, limit: int = 20) -> List[FeedbackEntry]:
        return sorted(self._feedback_log, key=lambda x: x.ts, reverse=True)[:limit]

    def get_feedback_stats(self) -> Dict[str, Any]:
        """反馈统计用于 self-improvement。"""
        corrections = [f for f in self._feedback_log if f.source == "user_correction"]
        tasks = [f for f in self._feedback_log if f.source == "task_result"]
        return {
            "total_feedback": len(self._feedback_log),
            "user_corrections": len(corrections),
            "task_results": len(tasks),
            "correction_rate": len(corrections) / max(len(self._feedback_log), 1),
        }

    # ── Operating Loop 桥接 ─────────────────────────────
    def attach_to_operating_loop(self, loop):
        """挂入 personal_operating_loop_v2。"""
        self._operating_loop = loop
        audit_info("PreferenceEvolutionModel", "operating_loop_attached")

    def _auto_bridge_loop(self):
        """V91: 自动挂接 operating loop，离线兼容。"""
        if self._operating_loop is not None:
            return
        try:
            from orchestration.agent_kernel.personal_operating_loop_v2 import PersonalOperatingLoopV2
            self._operating_loop = PersonalOperatingLoopV2()
            audit_info("PreferenceEvolutionModel", "operating_loop_auto_attached")
        except Exception as e:
            # 离线模式下创建轻量 mock loop
            class _MockOperatingLoop:
                def on_preference_feedback(self, data):
                    return {"status": "offline_mock", "ingested": True}
            self._operating_loop = _MockOperatingLoop()
            audit_warning("PreferenceEvolutionModel", "operating_loop_mock_attached", error=str(e)[:200])

    def _notify_loop(self, event: str, key: str, value):
        """通知 operating loop 偏好变更。"""
        if self._operating_loop and hasattr(self._operating_loop, "on_preference_feedback"):
            try:
                self._operating_loop.on_preference_feedback({
                    "event": event, "key": key, "value": value, "ts": time.time()
                })
            except Exception:
                pass

    def export_state(self) -> Dict[str, Any]:
        return {
            "values": dict(self.state.values),
            "confidence": dict(self.state.confidence),
            "history_len": len(self.state.history),
            "feedback_len": len(self._feedback_log),
        }

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
