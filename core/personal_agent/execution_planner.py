# -*- coding: utf-8 -*-
"""V86 execution planner.

Maps task graph nodes to model/tool/capability hints.  It does not execute
provider APIs; actual model choice is delegated to V85 core.llm when available.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .schemas import ExecutionPlan, NodeType, RiskLevel, TaskGraph


class ExecutionPlanner:
    def plan(self, graph: TaskGraph, context: Dict[str, Any] | None = None) -> ExecutionPlan:
        context = context or {}
        node_plans: Dict[str, Dict[str, Any]] = {}
        can_auto: List[str] = []
        approvals: List[str] = []
        blocked: List[str] = []
        gaps: List[Dict[str, Any]] = []

        for node in graph.nodes:
            route = self._route_for_node(node, graph.goal.raw_request, context)
            node.route_hint = route.get("route")
            node.model_hint = route.get("model")
            node.tool_hint = route.get("tool")
            node_plans[node.node_id] = route

            if node.requires_approval or node.risk_level in {RiskLevel.L3, RiskLevel.L4}:
                approvals.append(node.node_id)
            elif route.get("capability_gap"):
                gaps.append({"node_id": node.node_id, "missing": route.get("missing_capability")})
            elif node.risk_level in {RiskLevel.L0, RiskLevel.L1}:
                can_auto.append(node.node_id)
            else:
                blocked.append(node.node_id)

        return ExecutionPlan(
            graph_id=graph.graph_id,
            node_plans=node_plans,
            can_auto_run_nodes=can_auto,
            approval_nodes=approvals,
            blocked_nodes=blocked,
            capability_gaps=gaps,
        )

    def _route_for_node(self, node, raw_request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if node.node_type == NodeType.REASONING:
            return {"route": "reasoning", "model": self._llm_route(raw_request, has_tools=False), "tool": None}
        if node.node_type == NodeType.POLICY:
            return {"route": "policy_judge", "model": None, "tool": "core.personal_agent.PolicyJudge"}
        if node.node_type == NodeType.CAPABILITY_RESOLUTION:
            return {"route": "capability_registry", "model": None, "tool": "capabilities.registry"}
        if node.node_type == NodeType.MODEL_ROUTING:
            return {"route": "model_router", "model": self._llm_route(raw_request, has_tools=True), "tool": "core.llm.auto_route"}
        if node.node_type == NodeType.APPROVAL:
            return {"route": "approval_interrupt", "model": None, "tool": "capabilities.approve_action"}
        if node.node_type == NodeType.VERIFICATION:
            return {"route": "result_verifier", "model": self._llm_route(raw_request, has_tools=False), "tool": "core.personal_agent.ResultVerifier"}
        if node.node_type == NodeType.MEMORY_WRITEBACK:
            return {"route": "experience_writer", "model": None, "tool": "core.personal_agent.ExperienceWriter"}
        return {"route": "tool_execution", "model": self._llm_route(node.title, has_tools=True), "tool": "route_selector", "required_capabilities": node.required_capabilities}

    def _llm_route(self, query: str, has_tools: bool) -> str:
        try:
            from core.llm import auto_route
            decision = auto_route(query, has_tools=has_tools)
            return decision.model_name
        except Exception:
            return "LLM_ROUTER"
