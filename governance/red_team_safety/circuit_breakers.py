"""V80 runtime circuit breakers: cost caps, anomaly isolation and global kill switch."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Mapping


@dataclass(frozen=True)
class CircuitBreakerResult:
    status: str
    tripped: bool
    reason: str
    safe_mode: str
    allowed_real_side_effects: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CostCircuitBreaker:
    """Stops runaway calls before they can become spend.

    This breaker is intentionally not a billing connector. It only evaluates
    estimated local counters and can never perform a purchase/top-up.
    """

    def __init__(self, max_estimated_cost: float = 0.0, max_tool_calls: int = 64, max_loop_depth: int = 12) -> None:
        self.max_estimated_cost = max_estimated_cost
        self.max_tool_calls = max_tool_calls
        self.max_loop_depth = max_loop_depth

    def evaluate(self, telemetry: Mapping[str, Any] | None = None) -> CircuitBreakerResult:
        telemetry = dict(telemetry or {})
        estimated_cost = float(telemetry.get("estimated_cost", 0.0) or 0.0)
        tool_calls = int(telemetry.get("tool_calls", 0) or 0)
        loop_depth = int(telemetry.get("loop_depth", 0) or 0)
        payment_requested = bool(telemetry.get("payment_requested"))
        if payment_requested:
            return CircuitBreakerResult("tripped", True, "payment_or_topup_request_detected", "prepare_budget_request_only", details=dict(telemetry))
        if estimated_cost > self.max_estimated_cost:
            return CircuitBreakerResult("tripped", True, "estimated_cost_above_zero_pending_access_cap", "stop_and_request_manual_budget_approval", details=dict(telemetry))
        if tool_calls > self.max_tool_calls:
            return CircuitBreakerResult("tripped", True, "tool_call_limit_exceeded", "stop_loop_and_summarize", details=dict(telemetry))
        if loop_depth > self.max_loop_depth:
            return CircuitBreakerResult("tripped", True, "recursive_loop_depth_exceeded", "stop_loop_and_checkpoint", details=dict(telemetry))
        return CircuitBreakerResult("pass", False, "within_pending_access_budget_limits", "continue_sandbox_only", details=dict(telemetry))


class AnomalyContainment:
    """Converts suspicious runtime signals into isolation actions."""

    SUSPICIOUS_MARKERS = (
        "ignore previous", "ignore all rules", "bypass", "disable guardrails", "secret", "api key",
        "直接付款", "绕过", "忽略规则", "关闭安全", "发给外部", "验证码", "支付密码",
    )

    def evaluate(self, signals: Iterable[str] | None = None) -> Dict[str, Any]:
        raw = [str(s) for s in (signals or [])]
        text = "\n".join(raw).lower()
        hits = [marker for marker in self.SUSPICIOUS_MARKERS if marker.lower() in text]
        isolated = bool(hits)
        return {
            "status": "isolated" if isolated else "pass",
            "isolated": isolated,
            "matched_markers": hits,
            "actions": [
                "freeze_live_adapters",
                "disable_new_skill_promotion",
                "force_human_review",
                "write_incident_audit_event",
            ] if isolated else ["continue_sandbox_only"],
            "real_side_effects": 0,
        }


class GlobalKillSwitch:
    """Final operator override. It halts all execution layers, not just tools."""

    def __init__(self) -> None:
        self.armed = True
        self.triggered = False
        self.reason = ""

    def status(self) -> Dict[str, Any]:
        return {
            "armed": self.armed,
            "triggered": self.triggered,
            "reason": self.reason,
            "effect": "all_runtime_execution_halted" if self.triggered else "ready_to_halt",
            "real_side_effects": 0,
        }

    def trigger(self, reason: str) -> Dict[str, Any]:
        self.triggered = True
        self.reason = str(reason or "operator_triggered")
        return self.status()
