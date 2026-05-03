# -*- coding: utf-8 -*-
"""V86 result verifier."""
from __future__ import annotations

from .schemas import NodeStatus, TaskGraph, VerificationResult


class ResultVerifier:
    def verify(self, graph: TaskGraph) -> VerificationResult:
        completed = sum(1 for n in graph.nodes if n.status == NodeStatus.COMPLETED)
        blocked = sum(1 for n in graph.nodes if n.status in {NodeStatus.BLOCKED_APPROVAL, NodeStatus.BLOCKED_POLICY})
        failed = sum(1 for n in graph.nodes if n.status == NodeStatus.FAILED)
        total = max(len(graph.nodes), 1)
        score = round(max(0.0, (completed - failed * 2) / total), 3)

        reasons = []
        next_actions = []
        if failed:
            reasons.append("failed_nodes_exist")
            next_actions.append("retry_or_replan_failed_nodes")
        if blocked:
            reasons.append("approval_or_policy_block_exists")
            next_actions.append("request_user_approval_or_generate_safe_alternative")
        if completed == total:
            reasons.append("all_nodes_completed")
        if not reasons:
            reasons.append("partial_progress_without_failures")

        passed = failed == 0 and completed >= total - blocked
        return VerificationResult(
            graph_id=graph.graph_id,
            passed=passed,
            score=score,
            completed_nodes=completed,
            blocked_nodes=blocked,
            failed_nodes=failed,
            reasons=reasons,
            next_actions=next_actions,
        )
