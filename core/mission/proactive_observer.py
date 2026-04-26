from __future__ import annotations


class ProactiveObserver:
    """Observe available signals without pretending to have real permissions.

    Real integrations must bind through external connector registry.
    """

    def observe(self, context: dict | None = None) -> dict:
        ctx = context or {}
        signals = list(ctx.get("signals", []))
        return {
            "status": "observed",
            "signals": signals,
            "needs_attention": [s for s in signals if s.get("priority") in {"high", "urgent"}],
            "missing_integrations": ctx.get("missing_integrations", []),
            "side_effect": False,
        }
