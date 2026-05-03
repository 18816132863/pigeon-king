from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class TokenOptimizer:
    """V180: context/token optimizer."""
    def optimize(self, context_items: list[str], budget: int = 8000) -> IntelligenceArtifact:
        scored = sorted(context_items, key=lambda x: (("V" in x) + ("核心" in x), -len(x)), reverse=True)
        selected = []
        used = 0
        for item in scored:
            est = max(1, len(item) // 2)
            if used + est <= budget:
                selected.append(item)
                used += est
        reduction = 1 - (used / max(1, sum(max(1, len(x)//2) for x in context_items)))
        return IntelligenceArtifact(new_id("token"), "token_optimization", "token", IntelligenceStatus.READY, 0.9, {"selected": selected, "estimated_tokens": used, "reduction": round(reduction, 4)})
