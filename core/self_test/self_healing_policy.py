from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HealingAction:
    finding: str
    action: str
    safe_auto_apply: bool
    requires_review: bool
    rollback: str


class SelfHealingPolicy:
    """Map diagnostics findings to bounded, auditable healing actions."""

    def propose(self, finding_name: str, severity: str = "warning") -> HealingAction:
        if "pollution" in finding_name:
            return HealingAction(
                finding=finding_name,
                action="remove_runtime_pollution_from_package",
                safe_auto_apply=True,
                requires_review=False,
                rollback="restore_from_clean_baseline_zip",
            )
        if "registry" in finding_name or "fusion" in finding_name:
            return HealingAction(
                finding=finding_name,
                action="recompute_registry_stats_without_changing_runtime_code",
                safe_auto_apply=True,
                requires_review=False,
                rollback="restore_previous_registry_json",
            )
        return HealingAction(
            finding=finding_name,
            action="open_review_ticket_and_block_release",
            safe_auto_apply=False,
            requires_review=True,
            rollback="no_auto_change",
        )
