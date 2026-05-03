from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .schemas import (
    ReleaseHardeningResult,
    CheckStatus,
    SnapshotStatus,
    RegressionStatus,
    GateStatus,
    ReleaseStatus,
    ProfileName,
    new_id,
)
from .environment_doctor import EnvironmentDoctor
from .config_contract import ConfigContractManager
from .dependency_guard import DependencyGuard
from .snapshot_manager import SnapshotManager
from .rollback_manager import RollbackManager
from .regression_matrix import RegressionMatrix
from .release_manifest import ReleaseManifestBuilder
from .deployment_profile import DeploymentProfileManager
from .runtime_report import RuntimeReporter


class ReleaseHardeningKernel:
    """V136: one-shot release hardening orchestrator."""

    def __init__(self, root: str | Path = ".", state_root: str | Path = ".release_hardening_state"):
        self.root = Path(root)
        self.state_root = Path(state_root)
        self.env = EnvironmentDoctor(self.root)
        self.config = ConfigContractManager(self.state_root)
        self.deps = DependencyGuard(self.state_root)
        self.snapshot = SnapshotManager(self.root, self.state_root)
        self.rollback = RollbackManager()
        self.regression = RegressionMatrix()
        self.manifest = ReleaseManifestBuilder(self.root)
        self.profile = DeploymentProfileManager()
        self.reporter = RuntimeReporter()

    def run_cycle(self, goal: str, profile_name: ProfileName = ProfileName.LOCAL) -> ReleaseHardeningResult:
        run_id = new_id("release")
        env = self.env.check()
        config = self.config.evaluate()
        dep_results = self.deps.check_all()
        dep_status = self.deps.overall_status(dep_results)
        snapshot = self.snapshot.create_manifest()
        rollback = self.rollback.build_plan(snapshot)
        regression = self.regression.run()
        manifest = self.manifest.build()
        deploy = self.profile.build(
            name=profile_name,
            regression_pass=regression.status == RegressionStatus.PASS,
            snapshot_ready=snapshot.status == SnapshotStatus.CREATED,
        )

        checks = {
            "environment": env.status.value,
            "config": config.status.value,
            "dependencies": dep_status.value,
            "snapshot": snapshot.status.value,
            "regression": regression.status.value,
            "manifest": manifest.status.value,
            "deployment_gate": deploy.gate_status.value,
        }
        runtime = self.reporter.build(manifest.id, checks)

        # Local profile may be ready even with pycache warnings; prod is stricter.
        if deploy.gate_status == GateStatus.CLOSED or runtime.status == ReleaseStatus.BLOCKED:
            status = ReleaseStatus.BLOCKED
            next_action = "修复关闭的发布门禁后再覆盖"
        elif deploy.gate_status == GateStatus.WARN or runtime.status == ReleaseStatus.DEGRADED_READY:
            status = ReleaseStatus.DEGRADED_READY
            next_action = "可在本地/灰度执行，生产前需人工确认"
        else:
            status = ReleaseStatus.READY
            next_action = "可执行覆盖并运行验证脚本"

        return ReleaseHardeningResult(
            run_id=run_id,
            goal=goal,
            release_status=status,
            env_status=env.status,
            config_status=config.status,
            dependency_status=dep_status,
            snapshot_status=snapshot.status,
            regression_status=regression.status,
            deployment_gate=deploy.gate_status,
            score=runtime.score,
            next_action=next_action,
            details={
                "runtime_summary": runtime.summary,
                "rollback_commands": rollback.commands,
                "manifest_modules": len(manifest.modules),
                "manifest_scripts": len(manifest.scripts),
                "pycache_count": env.pycache_count,
                "deployment_profile": deploy.name.value,
                "deployment_notes": deploy.notes,
            },
        )


_DEFAULT: Optional[ReleaseHardeningKernel] = None


def init_release_hardening(root: str | Path = ".", state_root: str | Path = ".release_hardening_state") -> Dict:
    global _DEFAULT
    _DEFAULT = ReleaseHardeningKernel(root, state_root)
    return {"status": "ok", "root": str(Path(root)), "state_root": str(Path(state_root)), "modules": 10}


def run_release_hardening_cycle(goal: str, profile_name: ProfileName = ProfileName.LOCAL, root: str | Path = ".", state_root: str | Path = ".release_hardening_state") -> ReleaseHardeningResult:
    global _DEFAULT
    if _DEFAULT is None or _DEFAULT.root != Path(root) or _DEFAULT.state_root != Path(state_root):
        _DEFAULT = ReleaseHardeningKernel(root, state_root)
    return _DEFAULT.run_cycle(goal, profile_name=profile_name)
