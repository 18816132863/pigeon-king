from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import SkillLifecycleRecord, SkillLifecycleStatus, new_id, to_dict
from .storage import JsonStore


class SkillLifecycleManager:
    """V124: skill lifecycle from proposal to canary to active/rollback."""

    def __init__(self, root: str | Path = ".operating_spine_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "skill_lifecycle_records.json")

    def propose(self, skill_name: str, version: str) -> SkillLifecycleRecord:
        rec = SkillLifecycleRecord(
            id=new_id("skill"),
            skill_name=skill_name,
            status=SkillLifecycleStatus.PROPOSED,
            version=version,
            canary_score=0.0,
            rollback_plan=f"disable {skill_name}@{version}; restore previous manifest",
            notes=["proposed"],
        )
        self.store.append(to_dict(rec))
        return rec

    def canary(self, record_id: str, score: float) -> SkillLifecycleRecord:
        data = self.store.read([])
        for item in data:
            if item["id"] == record_id:
                item["canary_score"] = score
                if score >= 0.9:
                    item["status"] = SkillLifecycleStatus.ACTIVE.value
                    item.setdefault("notes", []).append("promoted_active")
                elif score >= 0.7:
                    item["status"] = SkillLifecycleStatus.CANARY.value
                    item.setdefault("notes", []).append("kept_canary")
                else:
                    item["status"] = SkillLifecycleStatus.ROLLED_BACK.value
                    item.setdefault("notes", []).append("rolled_back_low_score")
                self.store.write(data)
                return self._from_dict(item)
        raise KeyError(f"unknown record_id: {record_id}")

    def active_count(self) -> int:
        return sum(1 for x in self.store.read([]) if x.get("status") == SkillLifecycleStatus.ACTIVE.value)

    def _from_dict(self, item: Dict) -> SkillLifecycleRecord:
        return SkillLifecycleRecord(
            id=item["id"],
            skill_name=item["skill_name"],
            status=SkillLifecycleStatus(item["status"]),
            version=item["version"],
            canary_score=float(item.get("canary_score", 0.0)),
            rollback_plan=item.get("rollback_plan", ""),
            notes=list(item.get("notes", [])),
        )
