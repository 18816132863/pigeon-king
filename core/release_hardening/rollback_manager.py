from __future__ import annotations

from pathlib import Path
from .schemas import RollbackPlan, SnapshotRecord, SnapshotStatus, new_id


class RollbackManager:
    """V131: deterministic rollback plan generator."""

    def build_plan(self, snapshot: SnapshotRecord) -> RollbackPlan:
        reversible = snapshot.status == SnapshotStatus.CREATED and snapshot.tracked_files > 0
        commands = [
            f"# inspect snapshot manifest: {snapshot.manifest_path}",
            "python -S scripts/v136_verify_release_hardening_upgrade.py",
        ]
        if reversible:
            commands.append("# restore changed files from backup/full workspace archive if verification fails")
        else:
            commands.append("# no snapshot files tracked; fallback to full workspace backup")
        return RollbackPlan(
            id=new_id("rollback"),
            snapshot_id=snapshot.id,
            reversible=reversible,
            commands=commands,
            notes=["rollback plan generated before release promotion"],
        )
