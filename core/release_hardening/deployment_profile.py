from __future__ import annotations

from .schemas import DeploymentProfile, ProfileName, GateStatus, new_id


class DeploymentProfileManager:
    """V134: deployment profile gates."""

    def build(self, name: ProfileName, regression_pass: bool, snapshot_ready: bool) -> DeploymentProfile:
        if name == ProfileName.PROD:
            require_approval = True
            require_snapshot = True
            require_regression = True
            allowed_risk = "L2"
        elif name == ProfileName.CANARY:
            require_approval = True
            require_snapshot = True
            require_regression = True
            allowed_risk = "L3"
        elif name == ProfileName.DEV:
            require_approval = False
            require_snapshot = False
            require_regression = True
            allowed_risk = "L3"
        else:
            require_approval = False
            require_snapshot = False
            require_regression = False
            allowed_risk = "L4_local_only"

        gates = []
        if require_snapshot and not snapshot_ready:
            gates.append("snapshot_missing")
        if require_regression and not regression_pass:
            gates.append("regression_failed")

        if gates:
            gate = GateStatus.CLOSED
        elif name in {ProfileName.PROD, ProfileName.CANARY}:
            gate = GateStatus.WARN
        else:
            gate = GateStatus.OPEN

        return DeploymentProfile(
            id=new_id("profile"),
            name=name,
            allowed_risk=allowed_risk,
            require_approval=require_approval,
            require_snapshot=require_snapshot,
            require_regression_pass=require_regression,
            gate_status=gate,
            notes=gates,
        )
