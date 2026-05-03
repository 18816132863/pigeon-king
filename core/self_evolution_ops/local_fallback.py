from __future__ import annotations

from .schemas import FallbackPlan, new_id


class LocalFallbackPlanner:
    """V112: local/offline fallback planner."""

    def plan(self, unavailable_capability: str) -> FallbackPlan:
        if unavailable_capability in {"web_search", "current_info"}:
            mode = "degraded_static_knowledge"
            steps = [
                "state that current lookup is unavailable",
                "use cached/internal knowledge only",
                "mark result as needing later verification",
            ]
            quality = 0.55
            notice = True
        elif unavailable_capability in {"model_api", "remote_llm"}:
            mode = "local_rule_based"
            steps = [
                "use deterministic rules",
                "avoid high-risk execution",
                "queue task for model-backed retry",
            ]
            quality = 0.45
            notice = True
        elif unavailable_capability in {"image_generation", "video_generation"}:
            mode = "script_or_prompt_only"
            steps = [
                "produce generation prompt/storyboard",
                "do not claim media artifact was generated",
                "save request for later media model execution",
            ]
            quality = 0.50
            notice = True
        else:
            mode = "manual_handoff"
            steps = [
                "explain missing capability",
                "offer safe manual procedure",
                "record capability gap",
            ]
            quality = 0.40
            notice = True

        return FallbackPlan(
            id=new_id("fallback"),
            unavailable_capability=unavailable_capability,
            fallback_mode=mode,
            steps=steps,
            quality_expected=quality,
            needs_user_notice=notice,
        )
