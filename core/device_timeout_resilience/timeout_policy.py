from __future__ import annotations

from .schemas import TimeoutPolicy


class TimeoutPolicyEngine:
    """Central timeout policy.

    The key rule: never let a single external/device connector call consume the
    platform hard timeout. It must return before the soft deadline with a
    checkpoint and resumable state.
    """

    def __init__(self, policy: TimeoutPolicy | None = None):
        self.policy = policy or TimeoutPolicy()

    def classify(self, message: str, estimated_seconds: int) -> dict:
        long_running = estimated_seconds >= self.policy.soft_deadline_seconds
        needs_approval = any(x in message for x in ["设备", "手机", "点击", "打开应用", "发送", "写入日程", "删除", "安装", "付款", "转账"])
        connector_risky = any(x in message for x in ["Calendar", "日程", "Gmail", "邮件", "端侧", "设备", "手机"])
        return {
            "long_running": long_running,
            "needs_approval": needs_approval,
            "connector_risky": connector_risky,
            "mode": "chunked_fast_ack" if long_running else "direct_safe",
            "soft_deadline_seconds": self.policy.soft_deadline_seconds,
            "max_step_seconds": self.policy.max_step_seconds,
        }

    def safe_single_call_budget(self) -> int:
        return min(self.policy.max_step_seconds, self.policy.soft_deadline_seconds - 5)
