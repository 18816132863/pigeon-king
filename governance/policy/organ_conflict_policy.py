"""
V23.6 Organ Conflict Policy.

器官 = capability organ / ability group.
器官不是架构层。  This policy prevents future modules from turning organs into
extra layers or bypassing the proper layer owners.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

ORGAN_OWNER = {
    "goal_compiler": "L3 Orchestration",
    "task_graph": "L3 Orchestration",
    "agent_kernel": "L3 Orchestration",
    "memory_kernel": "L2 Memory Context",
    "persona_kernel": "L2 Memory Context + L3 Orchestration",
    "unified_judge": "L5 Governance",
    "risk_matrix": "L5 Governance",
    "execution_outbox": "L4 Execution",
    "device_action": "L4 Execution",
    "context_resume": "L6 Infrastructure",
    "snapshot": "L6 Infrastructure",
}


@dataclass(frozen=True)
class OrganConflictCheck:
    organ: str
    owner: str
    conflict: bool
    rule: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def check_organ_owner(organ: str, declared_owner: str) -> OrganConflictCheck:
    expected = ORGAN_OWNER.get(organ, "UNKNOWN")
    conflict = expected != "UNKNOWN" and declared_owner != expected
    return OrganConflictCheck(
        organ=organ,
        owner=expected,
        conflict=conflict,
        rule="organs are ability groups owned by one of the six architecture layers; they are not L7",
    )


def check_all_default_organs() -> Dict[str, object]:
    checks: List[Dict[str, object]] = []
    for organ, owner in ORGAN_OWNER.items():
        checks.append(check_organ_owner(organ, owner).to_dict())
    return {"passed": not any(c["conflict"] for c in checks), "checks": checks}
