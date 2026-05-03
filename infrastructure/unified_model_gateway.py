from __future__ import annotations

import os
from typing import Any, Dict


def model_calls_disabled() -> bool:
    return (
        os.environ.get("NO_EXTERNAL_API", "true").lower() == "true"
        or os.environ.get("DISABLE_LLM_API", "true").lower() == "true"
        or os.environ.get("DISABLE_THINKING_MODE", "true").lower() == "true"
    )


class UnifiedModelGateway:
    """Single model gateway. No direct provider call is allowed in offline mode."""

    def call_model(self, prompt: str, model: str | None = None, purpose: str = "reasoning", **kwargs: Any) -> Dict[str, Any]:
        if model_calls_disabled():
            return {
                "status": "blocked",
                "mode": "offline_mock",
                "model": model or "mock-local",
                "purpose": purpose,
                "external_api_calls": 0,
                "real_side_effects": 0,
                "requires_api": False,
                "blocked_reason": "NO_EXTERNAL_API_or_DISABLE_LLM_API_or_DISABLE_THINKING_MODE",
                "result": {"summary": "external model call blocked; use local reasoning/context only"},
            }
        return {
            "status": "deferred",
            "mode": "requires_explicit_live_adapter",
            "model": model,
            "purpose": purpose,
            "external_api_calls": 0,
            "blocked_reason": "live_model_not_bound",
        }

    def embedding(self, text: str, model: str | None = None, **kwargs: Any) -> Dict[str, Any]:
        if model_calls_disabled():
            # deterministic tiny local fallback; enough for dry-run/gates, not a real embedding
            seed = sum(ord(c) for c in str(text)[:256]) % 997
            vec = [((seed + i * 17) % 101) / 100.0 for i in range(16)]
            return {"status": "ok", "mode": "offline_mock_embedding", "vector": vec, "external_api_calls": 0, "requires_api": False}
        return {"status": "deferred", "mode": "requires_explicit_live_embedding_adapter", "external_api_calls": 0}


def call_model(prompt: str, model: str | None = None, purpose: str = "reasoning", **kwargs: Any) -> Dict[str, Any]:
    return UnifiedModelGateway().call_model(prompt, model, purpose, **kwargs)


def embed(text: str, model: str | None = None, **kwargs: Any) -> Dict[str, Any]:
    return UnifiedModelGateway().embedding(text, model, **kwargs)
