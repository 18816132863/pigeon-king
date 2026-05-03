from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class PortfolioManager:
    """V168: capability portfolio manager."""
    def build(self, features: list[dict]) -> IntelligenceArtifact:
        buckets = {"core": [], "ops": [], "risk": [], "reporting": []}
        for f in features:
            theme = f.get("theme", "")
            if "风险" in theme or "合规" in theme:
                buckets["risk"].append(f)
            elif "看板" in theme or "输出" in theme:
                buckets["reporting"].append(f)
            elif "运营" in theme or "数据" in theme or "成本" in theme:
                buckets["ops"].append(f)
            else:
                buckets["core"].append(f)
        score = 0.9 if sum(len(v) for v in buckets.values()) == len(features) else 0.7
        return IntelligenceArtifact(new_id("portfolio"), "capability_portfolio", "portfolio", IntelligenceStatus.READY, score, {"buckets": buckets})
