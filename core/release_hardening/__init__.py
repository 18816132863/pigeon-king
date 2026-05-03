"""
V127-V136 Release Hardening Upgrade.

This package turns the agent stack into a deployable, recoverable release unit.

V127 Environment Doctor
V128 Config Contract
V129 Dependency Guard
V130 Snapshot Manager
V131 Rollback Manager
V132 Regression Matrix
V133 Release Manifest
V134 Deployment Profile
V135 Runtime Report
V136 Release Hardening Kernel
"""

from .schemas import (
    CheckStatus,
    ProfileName,
    GateStatus,
    SnapshotStatus,
    RegressionStatus,
    ReleaseStatus,
    EnvironmentCheck,
    ConfigContract,
    DependencyCheck,
    SnapshotRecord,
    RollbackPlan,
    RegressionCase,
    RegressionSuiteResult,
    ReleaseManifest,
    DeploymentProfile,
    RuntimeReport,
    ReleaseHardeningResult,
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
from .release_hardening_kernel import ReleaseHardeningKernel, init_release_hardening, run_release_hardening_cycle

__all__ = [
    "CheckStatus",
    "ProfileName",
    "GateStatus",
    "SnapshotStatus",
    "RegressionStatus",
    "ReleaseStatus",
    "EnvironmentCheck",
    "ConfigContract",
    "DependencyCheck",
    "SnapshotRecord",
    "RollbackPlan",
    "RegressionCase",
    "RegressionSuiteResult",
    "ReleaseManifest",
    "DeploymentProfile",
    "RuntimeReport",
    "ReleaseHardeningResult",
    "EnvironmentDoctor",
    "ConfigContractManager",
    "DependencyGuard",
    "SnapshotManager",
    "RollbackManager",
    "RegressionMatrix",
    "ReleaseManifestBuilder",
    "DeploymentProfileManager",
    "RuntimeReporter",
    "ReleaseHardeningKernel",
    "init_release_hardening",
    "run_release_hardening_cycle",
]
