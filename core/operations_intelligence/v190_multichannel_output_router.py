from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class MultiChannelOutputRouter:
    """V190: multi-channel output router."""
    def route(self, audience: str, content_type: str) -> IntelligenceArtifact:
        if audience in {"大龙虾", "technical_executor"}:
            channel = "zip_plus_one_command"
            format_ = "short_command_first"
        elif audience in {"直播运营团队", "operator"}:
            channel = "operator_brief"
            format_ = "checklist_and_script"
        elif audience in {"boss", "executive"}:
            channel = "executive_summary"
            format_ = "one_page_summary"
        else:
            channel = "chat"
            format_ = "concise_markdown"
        return IntelligenceArtifact(new_id("router"), "multichannel_output_route", "output", IntelligenceStatus.READY, 0.89, {"audience": audience, "content_type": content_type, "channel": channel, "format": format_})
