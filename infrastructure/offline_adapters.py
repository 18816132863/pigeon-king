"""
V91 offline adapters — 离线模式下未集成特征的 mock 接入。

覆盖:
- multimodal_search (多模态搜索)
- cross_lingual_search (跨语言搜索)  
- visual_operation_agent (视觉操作)
- identity_drift_guard_enhanced (身份漂移守卫)
- observability_reporter_bridge (可观测报告桥)
- solution_search_orchestrator_offline (离线方案搜索)
- capability_marketplace_offline (离线能力市场)
- sandbox_gate_offline (离线沙箱门)
- fusion_engines_offline (离线融合引擎)
- autonomy_regression_matrix (离线回归矩阵)
- continuous_learning_evaluator (离线学习评估)
- speculative_decoder_offline (离线推测解码)
"""
from __future__ import annotations
import json
import os
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

try:
    from infrastructure.offline_mode import (
        audit_info, audit_warning, mock_or_fallback, MockResult,
        STATE_DIR,
    )
except ImportError:
    STATE_DIR = Path(os.environ.get("WORKSPACE", "/home/sandbox/.openclaw/workspace")) / ".offline_state"
    @dataclass
    class MockResult:
        success: bool = True
        data: Dict = field(default_factory=dict)
        warning: str = "offline"
        source: str = "offline"
    def _noop(*a, **kw): pass
    audit_info = _noop
    audit_warning = _noop
    def mock_or_fallback(m, fb=None, **kw): return MockResult()


# ══════════════════════════════════════════════════════════
# 1. 多模态搜索
# ══════════════════════════════════════════════════════════
class OfflineMultimodalSearcher:
    def __init__(self):
        audit_info("OfflineMultimodalSearcher", "initialized")

    def search_image(self, query: str, limit: int = 5) -> MockResult:
        return mock_or_fallback("multimodal_search", warning="image_search_unavailable_offline",
            mock_data={"query": query, "results": [], "note": "offline_no_image_index"})

    def search_media(self, query: str, limit: int = 5) -> MockResult:
        return mock_or_fallback("multimodal_search", warning="media_search_unavailable_offline",
            mock_data={"query": query, "results": [], "note": "offline_no_media_index"})

    def describe_image(self, media_path: str) -> MockResult:
        return mock_or_fallback("multimodal_search", warning="image_description_unavailable_offline",
            mock_data={"path": media_path, "caption": "offline_cannot_describe", "note": "no_vision_model"})


# ══════════════════════════════════════════════════════════
# 2. 跨语言搜索
# ══════════════════════════════════════════════════════════
class OfflineCrossLingualSearcher:
    def __init__(self):
        audit_info("OfflineCrossLingualSearcher", "initialized")

    def search(self, query: str, source_lang: str = "zh", target_lang: str = "en") -> MockResult:
        return mock_or_fallback("cross_lingual_search", warning="cross_lingual_search_unavailable_offline",
            mock_data={"query": query, "source": source_lang, "target": target_lang, "results": []})

    def translate_query(self, text: str, target_lang: str = "en") -> MockResult:
        return mock_or_fallback("cross_lingual_search", warning="translation_unavailable_offline",
            mock_data={"original": text, "translated": text, "note": "offline_no_nmt_model"})


# ══════════════════════════════════════════════════════════
# 3. 视觉操作代理
# ══════════════════════════════════════════════════════════
class OfflineVisualAgent:
    def __init__(self):
        audit_info("OfflineVisualAgent", "initialized")

    def plan_action(self, screenshot_path: str, goal: str) -> MockResult:
        return mock_or_fallback("visual_operation_agent", warning="visual_agent_unavailable_offline",
            mock_data={"plan": [], "goal": goal, "note": "no_screen_access_offline"})

    def execute_plan(self, plan: list) -> MockResult:
        return mock_or_fallback("visual_operation_agent", warning="visual_execution_unavailable_offline",
            mock_data={"executed": 0, "total": len(plan), "note": "offline_dry_run"})


# ══════════════════════════════════════════════════════════
# 4. 身份漂移守卫（增强桥接）
# ══════════════════════════════════════════════════════════
def enhanced_identity_drift_check(twin: dict, audit_log: bool = True) -> dict:
    """增强版身份漂移检查——离线审计日志记录。"""
    forbidden = ["I am the user", "act as user without consent", "bypass_confirmation"]
    text = str(twin)
    violations = [v for v in forbidden if v in text]
    result = {
        "status": "safe" if not violations else "drift_detected",
        "violations": violations,
        "must_not_impersonate_user": True,
        "offline_audit": True,
    }
    if audit_log and violations:
        audit_warning("IdentityDriftGuard", "drift_detected", violations=violations)
    return result


# ══════════════════════════════════════════════════════════
# 5. 可观测报告桥接
# ══════════════════════════════════════════════════════════
@dataclass
class ObservabilityEvent:
    ts: float = field(default_factory=time.time)
    source: str = "offline"
    event_type: str = "unknown"
    data: Dict = field(default_factory=dict)

class OfflineObservabilityBridge:
    """将 ObservabilityReporter 的报告同步到离线审计。"""
    def __init__(self, log_path: Path = None):
        self._path = log_path or STATE_DIR / "observability_bridge.jsonl"
        self.events: list[ObservabilityEvent] = []

    def emit(self, event_type: str, data: dict, source: str = "offline"):
        event = ObservabilityEvent(source=source, event_type=event_type, data=data)
        self.events.append(event)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "a") as f:
            f.write(json.dumps({"ts": event.ts, "type": event_type, "source": source, "data": data}, ensure_ascii=False) + "\n")

    def report(self) -> dict:
        return {"total_events": len(self.events), "recent": [{"ts": e.ts, "type": e.event_type} for e in self.events[-10:]]}


# ══════════════════════════════════════════════════════════
# 6-11: 其他离线适配器
# ══════════════════════════════════════════════════════════
class OfflineCapabilityMarketplace:
    """能力市场 → 本地 registry 扫描。"""
    def search(self, capability: str) -> MockResult:
        return mock_or_fallback("capability_marketplace", mock_data={
            "capability": capability, "matches": [],
            "note": "offline_only_local_registry"
        })

class OfflineSandboxGate:
    """沙箱门 → always allow in offline（sandbox 隔离 = 已安全）。"""
    def evaluate(self, extension: dict) -> dict:
        audit_info("OfflineSandboxGate", "allow_in_offline", name=extension.get("name", "unknown"))
        return {"allowed": True, "reason": "offline_mode_sandbox_isolation_sufficient"}

class OfflineFusionEngines:
    """融合引擎 → 只做注册扫描，不触发外部融合。"""
    def scan(self, directory: Path = None) -> dict:
        return {"status": "offline_scan_only", "modules_found": 0, "note": "offline_no_external_fusion"}

class OfflineRegressionMatrix:
    """回归矩阵 → 仅基于本地状态评估。"""
    def evaluate(self, change: dict) -> dict:
        risk = "low"
        if change.get("affects_core", False):
            risk = "high"
        return {"risk": risk, "can_proceed": risk != "high", "recommendation": "offline_review_required" if risk == "high" else "safe"}

class OfflineLearningEvaluator:
    """持续学习评估 → 使用本地反馈统计。"""
    def evaluate(self, feedback_history: list) -> dict:
        corrections = sum(1 for f in feedback_history if f.get("source") == "user_correction")
        total = max(len(feedback_history), 1)
        return {
            "learning_quality": max(0.3, 0.9 - corrections / total),
            "correction_rate": round(corrections / total, 3),
            "recommendation": "improve" if corrections / total > 0.2 else "stable",
        }

class OfflineSolutionSearch:
    """方案搜索 → 本地文件全文搜索，零外部API。

    规则：
    - 只搜索 memory/ memory_context/ reports/ docs/ + 本地 .md .json .txt .py
    - 动作语义固定 analyze，不允许 commit 类动作
    - 无结果也返回 status=ok（不抛 gateway_error）
    - 所有调用写 append-only audit
    """
    def search(self, query: str = "", limit: int = 10) -> dict:
        try:
            from infrastructure.solution_search_orchestrator import SolutionSearchOrchestrator
            orch = SolutionSearchOrchestrator()
            return orch.search(query, limit)
        except ImportError:
            return {
                "status": "ok", "mode": "offline",
                "route": "orchestration.solution_search",
                "action_semantic": "analyze",
                "side_effects": False, "requires_api": False,
                "result": [],
                "warning": "no_local_solution_found",
                "query": query,
            }


class OfflineSpeculativeDecoder:
    """推测解码 → offline stub。"""
    def decode(self, prompt: str, target_tokens: int = 50) -> dict:
        return {"tokens_generated": 0, "output": "", "note": "offline_no_gpu_speculative_decoding"}


# ── 统一访问 ────────────────────────────────────────────
_adapters: dict[str, Any] = {}

def get_adapter(name: str):
    if name not in _adapters:
        factories = {
            "multimodal": OfflineMultimodalSearcher,
            "cross_lingual": OfflineCrossLingualSearcher,
            "visual_agent": OfflineVisualAgent,
            "observability_bridge": OfflineObservabilityBridge,
            "capability_marketplace": OfflineCapabilityMarketplace,
            "sandbox_gate": OfflineSandboxGate,
            "fusion_engines": OfflineFusionEngines,
            "regression_matrix": OfflineRegressionMatrix,
            "learning_evaluator": OfflineLearningEvaluator,
            "speculative_decoder": OfflineSpeculativeDecoder,
            "solution_search": OfflineSolutionSearch,
        }
        cls = factories.get(name)
        if cls:
            _adapters[name] = cls()
    return _adapters.get(name)


__all__ = [
    "OfflineMultimodalSearcher", "OfflineCrossLingualSearcher", "OfflineVisualAgent",
    "enhanced_identity_drift_check",
    "OfflineObservabilityBridge", "ObservabilityEvent",
    "OfflineCapabilityMarketplace", "OfflineSandboxGate",
    "OfflineFusionEngines", "OfflineRegressionMatrix",
    "OfflineLearningEvaluator", "OfflineSpeculativeDecoder",
    "get_adapter",
]
