from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional
from .schemas import CapabilityGap, CapabilityGapStatus, new_id


class CapabilityGapAnalyzer:
    """V89: capability gap detection and resolution planning."""

    def __init__(self, known_capabilities: Optional[Iterable[str]] = None):
        self.known_capabilities = set(known_capabilities or [
            "text_reasoning", "model_routing", "file_read", "document_search",
            "code_review", "task_graph", "risk_judge", "result_verify",
            "memory_write", "web_search", "image_generation", "video_generation",
        ])

    def infer_required_capabilities(self, goal: str) -> List[str]:
        g = goal.lower()
        required = ["text_reasoning", "task_graph", "risk_judge"]
        if any(x in goal for x in ["最新", "现在", "价格", "政策", "规则", "查一下"]):
            required.append("web_search")
        if any(x in goal for x in ["文件", "论文", "压缩包", "文档", "pdf", "docx"]):
            required.extend(["file_read", "document_search"])
        if any(x in goal for x in ["代码", "报错", "pytest", "接口", "模块"]):
            required.append("code_review")
        if any(x in goal for x in ["图片", "头像", "海报", "logo"]):
            required.append("image_generation")
        if any(x in goal for x in ["视频", "带货视频", "sora"]):
            required.append("video_generation")
        if any(x in goal for x in ["发邮件", "发送", "外部", "客户"]):
            required.append("external_action")
        if any(x in g for x in ["mcp", "connector", "api"]):
            required.append("connector_management")
        return sorted(set(required))

    def analyze(self, goal: str, available_capabilities: Optional[Iterable[str]] = None, connector_capabilities: Optional[Iterable[str]] = None) -> CapabilityGap:
        available = set(available_capabilities or self.known_capabilities)
        connector_caps = set(connector_capabilities or [])
        required = self.infer_required_capabilities(goal)
        missing = [x for x in required if x not in available]

        if not missing:
            status = CapabilityGapStatus.NO_GAP
            explanation = "All required capabilities are available locally."
        elif set(missing).issubset(connector_caps):
            status = CapabilityGapStatus.CAN_USE_CONNECTOR
            explanation = "Missing capabilities can be satisfied by registered connectors."
        elif any(x in connector_caps for x in missing):
            status = CapabilityGapStatus.CAN_USE_CONNECTOR
            explanation = "Some missing capabilities can be satisfied by connectors; remaining items need review."
        elif any(x in ["external_action", "connector_management"] for x in missing):
            status = CapabilityGapStatus.NEED_HUMAN
            explanation = "Goal requires sensitive or external capabilities; human approval or connector setup is required."
        else:
            status = CapabilityGapStatus.NEED_EXTENSION
            explanation = "Capabilities are missing and no connector can satisfy them."

        return CapabilityGap(
            id=new_id("gap"),
            requested_goal=goal,
            required_capabilities=required,
            missing_capabilities=missing,
            status=status,
            explanation=explanation,
        )
