from __future__ import annotations

from .version_lineage_tracker import VersionLineageTracker
from .upgrade_diff_risk_analyzer import UpgradeDiffRiskAnalyzer
from .rollback_snapshot_policy import RollbackSnapshotPolicy


class SelfUpgradeGovernor:
    """Govern the system's own upgrades before promotion."""

    def __init__(self) -> None:
        self.lineage = VersionLineageTracker()
        self.diff = UpgradeDiffRiskAnalyzer()
        self.snapshot = RollbackSnapshotPolicy()

    def govern(self, current: str, target: str, changed_modules: list[str]) -> dict:
        lineage = self.lineage.lineage(current, target)
        diff = self.diff.analyze(changed_modules)
        snapshot = self.snapshot.require_snapshot({"target": target})
        return {
            "status": "upgrade_governed",
            "lineage": lineage,
            "diff_risk": diff,
            "snapshot_policy": snapshot,
            "can_auto_promote": not diff["requires_full_tests"],
            "requires_user_review": diff["requires_full_tests"],
        }
