from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

from .schemas import ActionLogRecord, ActionLogStatus, new_id, to_dict
from .storage import JsonStore


class ActionLogStore:
    """Durable action log for real work entry."""

    def __init__(self, root: str | Path = ".real_work_entry_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "action_log.json")

    def record_from_trace(self, request_id: str, ai_result, trace) -> ActionLogRecord:
        task = next((n for n in ai_result.task_graph.nodes if n.id == trace.task_id), None)
        task_title = task.title if task else "unknown_task"

        if trace.status.value == "blocked":
            status = ActionLogStatus.BLOCKED
        elif trace.status.value == "waiting_approval":
            status = ActionLogStatus.WAITING_APPROVAL
        elif trace.status.value == "completed":
            status = ActionLogStatus.COMPLETED
        else:
            status = ActionLogStatus.RECORDED

        rec = ActionLogRecord(
            id=new_id("actionlog"),
            request_id=request_id,
            run_id=ai_result.run_id,
            task_id=trace.task_id,
            task_title=task_title,
            status=status,
            judge_decision=trace.decision.value,
            risk_level=ai_result.risk_level.value,
            checkpoint_id=ai_result.checkpoint_id,
            summary=trace.summary,
            evidence=trace.evidence,
        )
        self.store.append(to_dict(rec))
        return rec

    def list_for_request(self, request_id: str) -> List[Dict[str, Any]]:
        return [x for x in self.store.read([]) if x.get("request_id") == request_id]
