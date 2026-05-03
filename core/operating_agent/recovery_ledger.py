from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .schemas import RecoveryEntry, new_id, dataclass_to_dict
from .storage import JsonStore


class RecoveryLedger:
    """V104: transaction-like checkpoint and recovery ledger."""

    def __init__(self, root: str | Path = ".operating_agent_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "recovery_ledger.json")

    def record_checkpoint(self, run_id: str, action: str, checkpoint: Dict, rollback_plan: str, reversible: bool = True) -> RecoveryEntry:
        entry = RecoveryEntry(
            id=new_id("recovery"),
            run_id=run_id,
            action=action,
            checkpoint=checkpoint,
            rollback_plan=rollback_plan,
            reversible=reversible,
        )
        self.store.append(dataclass_to_dict(entry))
        return entry

    def list_run(self, run_id: str) -> List[RecoveryEntry]:
        return [self._from_dict(x) for x in self.store.read([]) if x.get("run_id") == run_id]

    def resume_hint(self, run_id: str) -> Dict:
        entries = self.list_run(run_id)
        if not entries:
            return {"can_resume": False, "reason": "no_checkpoint"}
        last = entries[-1]
        return {
            "can_resume": True,
            "last_action": last.action,
            "rollback_plan": last.rollback_plan,
            "reversible": last.reversible,
            "checkpoint": last.checkpoint,
        }

    def _from_dict(self, item: Dict) -> RecoveryEntry:
        return RecoveryEntry(
            id=item["id"],
            run_id=item["run_id"],
            action=item["action"],
            checkpoint=dict(item.get("checkpoint", {})),
            rollback_plan=item.get("rollback_plan", ""),
            reversible=bool(item.get("reversible", True)),
            created_at=float(item.get("created_at", 0.0)),
        )
