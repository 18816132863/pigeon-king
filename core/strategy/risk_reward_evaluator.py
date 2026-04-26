from __future__ import annotations


class RiskRewardEvaluator:
    """Evaluate goal value, risk, reversibility and learning value."""

    def evaluate(self, goal: str, plan: dict | None = None) -> dict:
        text = goal + " " + str(plan or {})
        blocked = any(k in text for k in ["违法", "绕过确认", "盗号", "支付密码"])
        high = any(k in text for k in ["支付", "发消息", "删除", "发布", "自动安装", "外部账号"])
        medium = any(k in text for k in ["接入", "搜索", "下载", "数据库", "API"])
        if blocked:
            risk = "BLOCKED"
        elif high:
            risk = "L3"
        elif medium:
            risk = "L2"
        else:
            risk = "L1"
        value = 80 if any(k in goal for k in ["自动", "长期", "提升", "赚钱", "学习", "运营"]) else 55
        reversibility = "low" if risk in {"L3", "L4", "BLOCKED"} else "high"
        return {
            "risk_level": risk,
            "value_score": value,
            "reversibility": reversibility,
            "learning_value": "high" if "越用越像" in goal or "长期" in goal else "medium",
            "decision": "block" if risk == "BLOCKED" else "consider",
        }
