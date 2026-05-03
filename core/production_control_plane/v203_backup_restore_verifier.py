from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, new_id

class BackupRestoreVerifier:
    """V203: backup/restore verification."""
    def verify(self, snapshot_count: int, restore_command_present: bool) -> ControlArtifact:
        score = (0.6 if snapshot_count > 0 else 0.0) + (0.4 if restore_command_present else 0.0)
        status = PlaneStatus.READY if score >= 0.9 else PlaneStatus.WARN
        return ControlArtifact(new_id("backup"), "backup_restore_verification", "backup", status, score, {"snapshots": snapshot_count, "restore_command_present": restore_command_present})
