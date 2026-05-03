"""
V91 Memory Writeback Guard V2 — 离线增强版。

- 保留现有使用点
- 新增 feedback tuner：ratio 0.85 可根据压实失败率、污染拦截率、用户纠错率自动微调
- JSONL 审计持久化
"""
from __future__ import annotations
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

try:
    from infrastructure.offline_mode import audit_info, audit_warning, STATE_DIR
except ImportError:
    STATE_DIR = Path(os.environ.get("WORKSPACE", "/home/sandbox/.openclaw/workspace")) / ".offline_state"
    def _noop(*a, **kw): pass
    audit_info = _noop
    audit_warning = _noop

ALLOWED_MEMORY_TYPES = {"semantic", "episodic", "procedural", "preference"}


@dataclass
class MemoryWritebackDecision:
    allowed: bool
    memory_type: str
    reason: str
    sanitized: Dict[str, object]

@dataclass
class WritebackStats:
    total_proposals: int = 0
    accepted: int = 0
    rejected: int = 0
    compaction_failures: int = 0   # 压实失败数
    pollution_intercepts: int = 0   # 污染拦截数
    user_corrections: int = 0       # 用户纠错数

@dataclass
class TuningState:
    ratio: float = 0.85
    pollution_ratio: float = 0.15  # 污染拦截率阈值
    min_confidence: Dict[str, float] = field(default_factory=lambda: {
        "semantic": 0.65, "episodic": 0.50, "procedural": 0.70, "preference": 0.60,
    })
    history: List[Dict] = field(default_factory=list)


class MemoryWritebackGuardV2:
    """V91 增强版 — 带 feedback tuner 的写回守卫。"""

    def __init__(self, state_path: Path = None):
        self.stats = WritebackStats()
        self.tuning = TuningState()
        self._state_path = state_path or STATE_DIR / "memory_writeback_guard_v2.json"
        self._audit_path = STATE_DIR / "memory_writeback_audit.jsonl"
        self._load_state()

    # ── 持久化 ──────────────────────────────────────────
    def _load_state(self):
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._state_path.exists():
            return
        try:
            data = json.loads(self._state_path.read_text())
            self.tuning.ratio = data.get("ratio", 0.85)
            self.tuning.pollution_ratio = data.get("pollution_ratio", 0.15)
            self.tuning.min_confidence = data.get("min_confidence", self.tuning.min_confidence)
            self.tuning.history = data.get("history", [])
            self.stats = WritebackStats(**data.get("stats", {}))
            audit_info("MemoryWritebackGuardV2", "state_loaded", ratio=self.tuning.ratio)
        except Exception as e:
            audit_warning("MemoryWritebackGuardV2", "state_load_failed", error=str(e))

    def _save_state(self):
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(json.dumps({
            "ratio": self.tuning.ratio,
            "pollution_ratio": self.tuning.pollution_ratio,
            "min_confidence": self.tuning.min_confidence,
            "history": self.tuning.history[-50:],
            "stats": {
                "total_proposals": self.stats.total_proposals,
                "accepted": self.stats.accepted,
                "rejected": self.stats.rejected,
                "compaction_failures": self.stats.compaction_failures,
                "pollution_intercepts": self.stats.pollution_intercepts,
                "user_corrections": self.stats.user_corrections,
            },
        }, ensure_ascii=False, indent=2))

    def _audit(self, decision: MemoryWritebackDecision, proposal: Dict):
        self._audit_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._audit_path, "a") as f:
            f.write(json.dumps({
                "ts": time.time(),
                "allowed": decision.allowed,
                "memory_type": decision.memory_type,
                "reason": decision.reason,
                "proposal_confidence": proposal.get("confidence"),
                "ratio": self.tuning.ratio,
            }, ensure_ascii=False) + "\n")

    # ── 核心评估 ────────────────────────────────────────
    def evaluate(self, proposal: Dict[str, object]) -> MemoryWritebackDecision:
        self.stats.total_proposals += 1
        memory_type = str(proposal.get("memory_type", "episodic"))

        if memory_type not in ALLOWED_MEMORY_TYPES:
            decision = MemoryWritebackDecision(False, memory_type, "unknown_memory_type", {})
            self.stats.rejected += 1
            self._audit(decision, proposal)
            return decision

        confidence = float(proposal.get("confidence", 0.0))
        min_conf = self.tuning.min_confidence.get(memory_type, 0.65)
        if confidence < min_conf:
            decision = MemoryWritebackDecision(False, memory_type, "low_confidence_for_long_term_memory", {})
            self.stats.rejected += 1
            self.stats.pollution_intercepts += 1
            self._audit(decision, proposal)
            return decision

        text = str(proposal.get("content", "")).strip()
        if not text:
            decision = MemoryWritebackDecision(False, memory_type, "empty_content", {})
            self.stats.rejected += 1
            self._audit(decision, proposal)
            return decision

        sanitized = {
            "memory_type": memory_type,
            "content": text[:2000],
            "source_goal_id": proposal.get("source_goal_id"),
            "confidence": confidence,
            "ttl_policy": proposal.get("ttl_policy", "reviewable"),
        }
        decision = MemoryWritebackDecision(True, memory_type, "allowed", sanitized)
        self.stats.accepted += 1
        self._audit(decision, proposal)
        return decision

    # ── Feedback Tuner ──────────────────────────────────
    def record_compaction_failure(self, proposal_id: str = None):
        """记录压实失败 → 可能需要降低 ratio。"""
        self.stats.compaction_failures += 1
        self._auto_tune()
        self._save_state()

    def record_pollution_intercept(self, proposal_id: str = None):
        """记录污染拦截 → 可能需要升高 min_confidence。"""
        self.stats.pollution_intercepts += 1
        self._auto_tune()
        self._save_state()

    def record_user_correction(self, memory_type: str, accepted: bool):
        """记录用户对记忆写入的纠错。"""
        self.stats.user_corrections += 1
        if not accepted:
            self.tuning.min_confidence[memory_type] = min(
                0.95, self.tuning.min_confidence.get(memory_type, 0.65) + 0.05
            )
        self._auto_tune()
        self._save_state()

    def _auto_tune(self):
        """根据压实失败率、污染拦截率、用户纠错率自动微调 ratio 和阈值。"""
        total = max(self.stats.total_proposals, 1)

        # 压实失败率 > 30% → 提高 ratio（更激进压缩）
        compaction_rate = self.stats.compaction_failures / total
        if compaction_rate > 0.3:
            self.tuning.ratio = min(0.95, self.tuning.ratio + 0.03)

        # 污染拦截率 > 20% → 各类型 min_confidence +0.03
        pollution_rate = self.stats.pollution_intercepts / total
        if pollution_rate > 0.2:
            for k in self.tuning.min_confidence:
                self.tuning.min_confidence[k] = min(0.95, self.tuning.min_confidence[k] + 0.03)

        # 用户纠错率高 → 提高对应类型的 min_confidence
        correction_rate = self.stats.user_corrections / total
        if correction_rate > 0.1:
            self.tuning.ratio = max(0.60, self.tuning.ratio - 0.02)  # 更保守

        self.tuning.history.append({
            "ts": time.time(), "ratio": self.tuning.ratio,
            "min_confidence": dict(self.tuning.min_confidence),
            "stats": {
                "compaction_rate": round(compaction_rate, 3),
                "pollution_rate": round(pollution_rate, 3),
                "correction_rate": round(correction_rate, 3),
            },
        })

    def get_tuning_report(self) -> Dict:
        return {
            "current_ratio": self.tuning.ratio,
            "min_confidence": dict(self.tuning.min_confidence),
            "stats": {
                "total": self.stats.total_proposals,
                "accepted": self.stats.accepted,
                "rejected": self.stats.rejected,
                "compaction_failures": self.stats.compaction_failures,
                "pollution_intercepts": self.stats.pollution_intercepts,
                "user_corrections": self.stats.user_corrections,
            },
            "history_len": len(self.tuning.history),
        }


# V91_VALID_LONG_TERM_MEMORY_FALLBACK_HELPER
def v91_valid_long_term_memory_fallback(content="", memory_type=""):
    """
    V91 本地兜底：只允许非敏感的长期偏好/画像/语义/流程记忆通过。
    不允许密码、token、验证码、支付凭证等敏感内容通过。
    """
    text = str(content).lower()
    target = str(memory_type).lower()
    sensitive = any(k in text for k in [
        "password", "passwd", "token", "secret", "api_key", "apikey",
        "验证码", "支付密码", "银行卡", "身份证", "credential", "private_key"
    ])
    long_term = any(k in target for k in [
        "long", "profile", "preference", "semantic", "procedure", "长期", "偏好", "画像"
    ])
    if long_term and not sensitive:
        return True, "v91_valid_long_term_memory_fallback"
    return False, "not_valid_long_term_or_sensitive"



def v92_valid_long_term_memory_fallback(content: str = "", memory_type: str = "long_term_memory", confidence: float = 0.80):
    """Allow valid non-sensitive long-term memories that were over-rejected by dynamic thresholds."""
    text = str(content).lower()
    target = str(memory_type).lower()
    sensitive = any(k in text for k in ["password","passwd","token","secret","api_key","apikey","credential","private_key","验证码","支付密码","银行卡","身份证","凭证","密钥"])
    long_term = any(k in target for k in ["long","profile","preference","semantic","procedure","长期","偏好","画像","事实","流程"])
    if long_term and not sensitive:
        return True, "v92_valid_long_term_memory_fallback"
    return False, "not_valid_long_term_or_sensitive"



def v92_tune_ratio(current_ratio: float = 0.85, false_reject_rate: float = 0.0, pollution_rate: float = 0.0, correction_rate: float = 0.0):
    old = current_ratio
    if false_reject_rate > 0.05 and pollution_rate < 0.01:
        current_ratio = max(0.70, current_ratio - 0.03)
    if pollution_rate > 0.02 or correction_rate > 0.10:
        current_ratio = min(0.95, current_ratio + 0.03)
    return {"status":"ok","old_ratio":old,"new_ratio":current_ratio,"side_effects":False}
