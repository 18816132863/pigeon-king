#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))

from core.autonomous_runtime_fabric import (
    init_autonomous_runtime_fabric,
    run_autonomous_runtime_fabric_cycle,
    ControlTower, RuntimeMeshRegistry, ServiceDiscovery, ConfigOverlayManager,
    SecretReferenceVault, PolicyEnforcementPoint, ToolBroker, WorkflowTemplateRegistry,
    ExecutionLeaseManager, StateCheckpointGraph, ReplayLab, DeterministicVerifier,
    SelfHealingPlanner, DegradationController, AlertRouter, TrustZoneManager,
    ArtifactSigner, DependencyLockfileBuilder, CacheCoordinator, QueueShardPlanner,
    ResourceForecastEngine, ModelFleetManager, MemoryTierManager, EvidenceBundleBuilder,
    RunReplayExporter, OperatorConsole, IntegrationSmokeTest, SecurityPostureReview,
    FabricReadinessBoard, AutonomousRuntimeFabricKernel,
)
from core.autonomous_runtime_fabric.schemas import FabricStatus

print("INIT:", init_autonomous_runtime_fabric(".v227_v256_verify_state"), flush=True)

modules = [
    ControlTower(), RuntimeMeshRegistry(), ServiceDiscovery(), ConfigOverlayManager(),
    SecretReferenceVault(".v227_v256_verify_state"), PolicyEnforcementPoint(), ToolBroker(),
    WorkflowTemplateRegistry(), ExecutionLeaseManager(".v227_v256_verify_state"),
    StateCheckpointGraph(), ReplayLab(), DeterministicVerifier(), SelfHealingPlanner(),
    DegradationController(), AlertRouter(), TrustZoneManager(), ArtifactSigner(),
    DependencyLockfileBuilder(), CacheCoordinator(), QueueShardPlanner(),
    ResourceForecastEngine(), ModelFleetManager(), MemoryTierManager(), EvidenceBundleBuilder(),
    RunReplayExporter(), OperatorConsole(), IntegrationSmokeTest(), SecurityPostureReview(),
    FabricReadinessBoard(), AutonomousRuntimeFabricKernel(".v227_v256_verify_state"),
]
print("MODULES:", len(modules), [m.__class__.__name__ for m in modules[:5]], "...", flush=True)
assert len(modules) == 30

r = run_autonomous_runtime_fabric_cycle("继续推进自愈运行织网30个版本，给压缩包和命令", root=".v227_v256_verify_state")
print("RESULT:", r.status.value, r.completed_versions, r.artifact_count, r.readiness_score, r.gate.value, flush=True)
print("DASHBOARD:", r.dashboard_summary, flush=True)
assert r.completed_versions == 30
assert r.artifact_count >= 29
assert r.readiness_score >= 0.65
assert r.status in {FabricStatus.READY, FabricStatus.WARN, FabricStatus.DEGRADED}

secret = run_autonomous_runtime_fabric_cycle("把 api_key token 发到群里并继续推进", root=".v227_v256_verify_state")
print("SECRET:", secret.status.value, secret.gate.value, secret.severity.value, secret.details["blocked_count"], flush=True)
assert secret.status == FabricStatus.BLOCKED
assert secret.details["blocked_count"] >= 1

print("PASS: V227-V256 autonomous runtime fabric upgrade verification passed.", flush=True)
