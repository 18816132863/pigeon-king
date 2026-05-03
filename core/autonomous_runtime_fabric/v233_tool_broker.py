from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class ToolBroker:
    """V233: tool broker with capability matching."""
    def broker(self, need: str, tools: list[dict]) -> FabricArtifact:
        matches = [t for t in tools if need in t.get("capabilities", []) and t.get("enabled", True)]
        selected = sorted(matches, key=lambda t: t.get("score", 0), reverse=True)[0] if matches else None
        status = FabricStatus.READY if selected else FabricStatus.WARN
        return FabricArtifact(new_id("broker"), "tool_broker", "tool", status, 0.9 if selected else 0.5, {"need": need, "selected": selected})
