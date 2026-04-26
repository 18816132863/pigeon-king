"""
V11.0 Strong Confirmation Gate

强确认不是“默认禁止”。它的作用是：
1. 高风险/副作用动作必须先生成确认摘要；
2. 未确认时返回 requires_confirmation，不直接执行；
3. 已确认后把确认 token 写入 params，允许执行或进入队列；
4. 超时/结果不确定时必须先核验结果，不能静默重试。
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
import hashlib
import json
import time


@dataclass
class ConfirmationDecision:
    allowed: bool
    status: str
    confirmation_level: str
    confirmation_token: Optional[str]
    reason: str
    preview: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_confirmation_token(action: str, payload: Dict[str, Any]) -> str:
    canonical = json.dumps({"action": action, "payload": payload}, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    return f"confirm:{action}:{digest}"


def require_strong_confirmation(
    *,
    action: str,
    payload: Dict[str, Any],
    provided_token: Optional[str] = None,
    risk_level: str = "L3",
    result_uncertain: bool = False,
) -> ConfirmationDecision:
    expected = build_confirmation_token(action, payload)
    high_risk = str(risk_level) in {"L3", "L4", "high", "critical"}

    preview = {
        "action": action,
        "risk_level": risk_level,
        "payload_summary": payload,
        "expected_confirmation_token": expected,
        "generated_at_ms": int(time.time() * 1000),
    }

    if result_uncertain:
        return ConfirmationDecision(
            allowed=False,
            status="hold_for_result_check",
            confirmation_level="strong_confirm",
            confirmation_token=expected,
            reason="上次结果不确定，必须先人工核验结果，不能直接重复执行",
            preview=preview,
        )

    if not high_risk:
        return ConfirmationDecision(True, "allowed", "none", None, "低风险动作允许自动执行", preview)

    if provided_token == expected:
        return ConfirmationDecision(True, "confirmed", "strong_confirm", expected, "强确认 token 匹配，允许继续", preview)

    return ConfirmationDecision(
        allowed=False,
        status="requires_confirmation",
        confirmation_level="strong_confirm",
        confirmation_token=expected,
        reason="需要强确认；不是默认禁止，确认后可继续执行",
        preview=preview,
    )
