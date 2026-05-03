# -*- coding: utf-8 -*-
"""V86 experience writer: durable procedure memory seed."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .schemas import ExperienceRecord, NodeStatus, TaskGraph, VerificationResult


class ExperienceWriter:
    def __init__(self, path: str | Path = ".v86_state/experience.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, graph: TaskGraph, verification: VerificationResult) -> ExperienceRecord:
        blocked_reasons = []
        for node in graph.nodes:
            if node.status in {NodeStatus.BLOCKED_APPROVAL, NodeStatus.BLOCKED_POLICY, NodeStatus.FAILED}:
                blocked_reasons.append(f"{node.node_id}:{node.status.value}:{node.error or (node.output or {}).get('reason', '')}")

        procedure = [
            "compile_goal",
            "judge_policy",
            "build_task_graph",
            "plan_execution",
            "run_safe_nodes",
            "verify_result",
            "write_experience",
        ]
        record = ExperienceRecord(
            graph_id=graph.graph_id,
            goal_id=graph.goal.goal_id,
            objective=graph.goal.objective,
            success=verification.passed,
            verification_score=verification.score,
            blocked_reasons=blocked_reasons,
            reusable_procedure=procedure,
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        return record
