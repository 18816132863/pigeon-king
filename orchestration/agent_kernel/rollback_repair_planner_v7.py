"""V74.0 Autonomous rollback and repair planner.

L3 chooses a repair path. L4 performs execution. L5 approves risky repair.
"""
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class FailureEvent:
    action_id: str
    failure_type: str
    reversible: bool = True
    has_evidence: bool = False
    side_effect: bool = False

class RollbackRepairPlanner:
    layer = "L3_ORCHESTRATION"

    def plan(self, event: FailureEvent) -> Dict[str, object]:
        if event.failure_type == "action_timeout":
            return {"next": "verify_before_retry", "allowed": True, "requires_confirmation": False}
        if event.side_effect and not event.has_evidence:
            return {"next": "collect_evidence", "allowed": True, "requires_confirmation": False}
        if event.reversible:
            return {"next": "rollback_then_retry_once", "allowed": True, "requires_confirmation": event.side_effect}
        return {"next": "manual_review", "allowed": False, "requires_confirmation": True}
