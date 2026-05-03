"""Rollback and recovery plan builder for pending-access missions."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping


@dataclass
class RollbackStep:
    node_id: str
    semantic_class: str
    strategy: str
    checkpoint_id: str
    live_undo_required: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RollbackPlanBuilder:
    def build(self, run: Mapping[str, Any]) -> Dict[str, Any]:
        steps: List[Dict[str, Any]] = []
        all_commit_mock = True
        for outcome in run.get("node_outcomes") or []:
            node = outcome.get("node") or {}
            semantic = (node.get("semantic") or {}).get("semantic_class", "unknown")
            node_id = str(node.get("node_id"))
            checkpoint = str((outcome.get("checkpoint") or {}).get("checkpoint_id") or f"ckpt_{node_id}")
            is_commit = bool((node.get("semantic") or {}).get("is_commit_action"))
            if is_commit:
                strategy = "no_live_undo_needed_commit_never_executed_restore_to_approval_packet"
                reason = "commit action was blocked and converted to approval/mock artifact"
                live_undo_required = False
                all_commit_mock = all_commit_mock and outcome.get("real_side_effect") is False
            else:
                strategy = "restore_from_checkpoint_and_replay_sandbox_trace"
                reason = "non-commit action may be retried in sandbox from checkpoint"
                live_undo_required = False
            steps.append(RollbackStep(node_id, semantic, strategy, checkpoint, live_undo_required, reason).to_dict())
        return {
            "status": "rollback_plan_ready" if steps and all(not step["live_undo_required"] for step in steps) else "incomplete",
            "step_count": len(steps),
            "all_commit_actions_mock_only": all_commit_mock,
            "live_undo_required": False,
            "steps": steps,
        }


def build_rollback_plan(run: Mapping[str, Any]) -> Dict[str, Any]:
    return RollbackPlanBuilder().build(run)
