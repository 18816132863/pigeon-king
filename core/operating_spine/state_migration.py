from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import MigrationRecord, MigrationStatus, new_id, to_dict
from .storage import JsonStore


class StateMigrationManager:
    """V118: schema/state migration manager for cross-version upgrades."""

    def __init__(self, root: str | Path = ".operating_spine_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "migration_records.json")

    def plan(self, from_version: str, to_version: str, required_files: List[str]) -> MigrationRecord:
        missing = [p for p in required_files if not Path(p).exists()]
        status = MigrationStatus.PLANNED if missing else MigrationStatus.NOT_NEEDED
        actions = [f"verify:{p}" for p in required_files]
        if missing:
            actions.extend([f"create_or_patch:{p}" for p in missing])
        record = MigrationRecord(
            id=new_id("migration"),
            from_version=from_version,
            to_version=to_version,
            status=status,
            files_checked=required_files,
            actions=actions,
            rollback_hint=f"restore snapshot before migrating {from_version}->{to_version}",
        )
        self.store.append(to_dict(record))
        return record

    def apply(self, record: MigrationRecord) -> MigrationRecord:
        status = MigrationStatus.APPLIED if record.status in {MigrationStatus.PLANNED, MigrationStatus.NOT_NEEDED} else MigrationStatus.FAILED
        applied = MigrationRecord(
            id=record.id,
            from_version=record.from_version,
            to_version=record.to_version,
            status=status,
            files_checked=record.files_checked,
            actions=record.actions + ["migration_marked_applied"],
            rollback_hint=record.rollback_hint,
            created_at=record.created_at,
        )
        data = self.store.read([])
        data = [to_dict(applied) if x.get("id") == applied.id else x for x in data]
        self.store.write(data)
        return applied

    def history(self) -> List[MigrationRecord]:
        return [self._from_dict(x) for x in self.store.read([])]

    def _from_dict(self, item: Dict) -> MigrationRecord:
        return MigrationRecord(
            id=item["id"],
            from_version=item["from_version"],
            to_version=item["to_version"],
            status=MigrationStatus(item["status"]),
            files_checked=list(item.get("files_checked", [])),
            actions=list(item.get("actions", [])),
            rollback_hint=item.get("rollback_hint", ""),
            created_at=float(item.get("created_at", 0.0)),
        )
