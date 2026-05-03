from __future__ import annotations


class PreferenceEvolution:
    """Update user preference signals from execution outcomes."""

    def evolve(self, old_model: dict | None, signal: dict) -> dict:
        model = dict(old_model or {})
        model.setdefault("preferred_style", "direct")
        model.setdefault("risk_preference", "bounded_high")
        model.setdefault("avoid", ["反复确认低风险事项", "没有判断的傻执行"])
        if signal.get("user_corrected"):
            model.setdefault("corrections", []).append(signal)
        if signal.get("success"):
            model.setdefault("successful_patterns", []).append(signal.get("pattern", "unknown"))
        return model
