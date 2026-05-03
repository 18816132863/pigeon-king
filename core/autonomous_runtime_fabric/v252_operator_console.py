from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class OperatorConsole:
    """V252: operator console data model."""
    def render(self, cards: dict[str, str]) -> FabricArtifact:
        warn = [k for k, v in cards.items() if v in {"warn", "degraded", "blocked"}]
        status = FabricStatus.WARN if warn else FabricStatus.READY
        score = 1 - len(warn) * 0.1
        return FabricArtifact(new_id("console"), "operator_console", "console", status, max(0.0, score), {"cards": cards, "attention": warn})
