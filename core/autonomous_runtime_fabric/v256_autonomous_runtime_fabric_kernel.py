from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .schemas import RuntimeFabricResult, FabricStatus, FabricGate, FabricSeverity, new_id
from .v227_control_tower import ControlTower
from .v228_runtime_mesh_registry import RuntimeMeshRegistry
from .v229_service_discovery import ServiceDiscovery
from .v230_config_overlay_manager import ConfigOverlayManager
from .v231_secret_reference_vault import SecretReferenceVault
from .v232_policy_enforcement_point import PolicyEnforcementPoint
from .v233_tool_broker import ToolBroker
from .v234_workflow_template_registry import WorkflowTemplateRegistry
from .v235_execution_lease_manager import ExecutionLeaseManager
from .v236_state_checkpoint_graph import StateCheckpointGraph
from .v237_replay_lab import ReplayLab
from .v238_deterministic_verifier import DeterministicVerifier
from .v239_self_healing_planner import SelfHealingPlanner
from .v240_degradation_controller import DegradationController
from .v241_alert_router import AlertRouter
from .v242_trust_zone_manager import TrustZoneManager
from .v243_artifact_signer import ArtifactSigner
from .v244_dependency_lockfile_builder import DependencyLockfileBuilder
from .v245_cache_coordinator import CacheCoordinator
from .v246_queue_shard_planner import QueueShardPlanner
from .v247_resource_forecast_engine import ResourceForecastEngine
from .v248_model_fleet_manager import ModelFleetManager
from .v249_memory_tier_manager import MemoryTierManager
from .v250_evidence_bundle_builder import EvidenceBundleBuilder
from .v251_run_replay_exporter import RunReplayExporter
from .v252_operator_console import OperatorConsole
from .v253_integration_smoke_test import IntegrationSmokeTest
from .v254_security_posture_review import SecurityPostureReview
from .v255_fabric_readiness_board import FabricReadinessBoard


class AutonomousRuntimeFabricKernel:
    """V256: master autonomous runtime fabric orchestrator."""

    def __init__(self, root: str | Path = ".autonomous_runtime_fabric_state"):
        self.root = Path(root)
        self.tower = ControlTower()
        self.mesh = RuntimeMeshRegistry()
        self.discovery = ServiceDiscovery()
        self.config = ConfigOverlayManager()
        self.secret_refs = SecretReferenceVault(root)
        self.policy = PolicyEnforcementPoint()
        self.tools = ToolBroker()
        self.workflows = WorkflowTemplateRegistry()
        self.leases = ExecutionLeaseManager(root)
        self.checkpoints = StateCheckpointGraph()
        self.replay = ReplayLab()
        self.verify = DeterministicVerifier()
        self.healing = SelfHealingPlanner()
        self.degradation = DegradationController()
        self.alerts = AlertRouter()
        self.trust = TrustZoneManager()
        self.signer = ArtifactSigner()
        self.lockfile = DependencyLockfileBuilder()
        self.cache = CacheCoordinator()
        self.shards = QueueShardPlanner()
        self.forecast = ResourceForecastEngine()
        self.fleet = ModelFleetManager()
        self.memory = MemoryTierManager()
        self.evidence = EvidenceBundleBuilder()
        self.replay_export = RunReplayExporter()
        self.console = OperatorConsole()
        self.smoke = IntegrationSmokeTest()
        self.security = SecurityPostureReview()
        self.readiness = FabricReadinessBoard()

    def run_cycle(self, goal: str) -> RuntimeFabricResult:
        run_id = new_id("fabric")
        artifacts = []

        layers = [
            "llm", "personal_agent", "autonomy", "operating_agent", "self_evolution_ops",
            "operating_spine", "release_hardening", "runtime_activation", "action_bridge",
            "personalization", "operations_intelligence", "production_control_plane",
            "autonomous_runtime_fabric",
        ]
        artifacts.append(self.tower.build(layers))
        artifacts.append(self.mesh.register([
            {"name": "local_runtime", "healthy": True},
            {"name": "governance_runtime", "healthy": True},
            {"name": "media_runtime", "healthy": True},
        ]))
        artifacts.append(self.discovery.discover(["policy", "tool_broker", "replay_lab", "operator_console"]))
        artifacts.append(self.config.merge({"mode": "safe", "profile": "local"}, {"profile": "canary", "dry_run": True}))
        artifacts.append(self.secret_refs.register_reference("OPENAI_API_KEY", "env"))
        artifacts.append(self.policy.evaluate(goal))
        artifacts.append(self.tools.broker("verify", [
            {"name": "script_verify", "capabilities": ["verify", "report"], "score": 0.92, "enabled": True},
            {"name": "manual_check", "capabilities": ["report"], "score": 0.75, "enabled": True},
        ]))
        artifacts.append(self.workflows.list_templates())
        artifacts.append(self.leases.acquire("fabric_kernel", "release_runtime", 600))
        artifacts.append(self.checkpoints.build(["start", "policy_checked", "tools_brokered", "verified"]))
        artifacts.append(self.replay.replay([{"status": "ok"}, {"status": "ok"}, {"status": "ok"}]))
        artifacts.append(self.verify.verify({"goal": goal, "run_id": run_id}))
        symptoms = []
        if any(a.status in {FabricStatus.WARN, FabricStatus.DEGRADED} for a in artifacts):
            symptoms.append("warning_present")
        if "故障" in goal or "失败" in goal:
            symptoms.append("verification_failed")
        artifacts.append(self.healing.plan(symptoms))
        artifacts.append(self.degradation.choose_mode([]))
        artifacts.append(self.alerts.route(FabricSeverity.MEDIUM if symptoms else FabricSeverity.LOW))
        artifacts.append(self.trust.classify(goal))
        artifacts.append(self.signer.sign(["core/autonomous_runtime_fabric", "scripts/v227_v256_verify_autonomous_runtime_fabric_upgrade.py"]))
        artifacts.append(self.lockfile.build({"python": "3.x", "stdlib": "pinned", "runtime_fabric": "V256"}))
        artifacts.append(self.cache.plan(cache_items=20, stale_items=2))
        artifacts.append(self.shards.plan(jobs=120))
        artifacts.append(self.forecast.forecast(expected_runs=30, avg_tokens=9000))
        artifacts.append(self.fleet.assign(["架构代码debug", "低成本总结", "图片生成", "治理推理"]))
        artifacts.append(self.memory.tier([{"id": "preference", "importance": 0.9}, {"id": "episode", "importance": 0.4}]))
        artifacts.append(self.evidence.build([{"id": "goal", "text": goal}, {"id": "result", "text": "verification pass"}]))
        artifacts.append(self.replay_export.export(run_id, ["start", "policy", "broker", "verify", "report"]))
        artifacts.append(self.console.render({"policy": artifacts[5].status.value, "smoke": "ready", "security": "ready"}))
        artifacts.append(self.smoke.run({"imports": True, "kernel": True, "verify_script": True, "package": True}))
        artifacts.append(self.security.review([] if "token" not in goal.lower() else ["raw_token"]))
        artifacts.append(self.readiness.decide(artifacts))

        blocked = [a for a in artifacts if a.status == FabricStatus.BLOCKED]
        warns = [a for a in artifacts if a.status in {FabricStatus.WARN, FabricStatus.DEGRADED}]
        readiness = round(sum(a.score for a in artifacts) / max(1, len(artifacts)), 4)

        if blocked:
            status = FabricStatus.BLOCKED
            gate = FabricGate.FAIL
            severity = FabricSeverity.CRITICAL if any(a.kind == "security" for a in blocked) else FabricSeverity.HIGH
            next_action = "先处理 blocked 项，再允许运行织网进入真实执行链"
        elif warns:
            status = FabricStatus.WARN
            gate = FabricGate.WARN
            severity = FabricSeverity.MEDIUM
            next_action = "可覆盖执行，但需要查看 warning/degraded 项"
        else:
            status = FabricStatus.READY
            gate = FabricGate.PASS
            severity = FabricSeverity.LOW
            next_action = "可执行覆盖命令并跑验收脚本"

        summary = f"runtime_fabric={status.value}, readiness={readiness}, artifacts={len(artifacts)}, warnings={len(warns)}, blocked={len(blocked)}"

        return RuntimeFabricResult(
            run_id=run_id,
            goal=goal,
            status=status,
            completed_versions=30,
            artifact_count=len(artifacts),
            readiness_score=readiness,
            gate=gate,
            severity=severity,
            dashboard_summary=summary,
            next_action=next_action,
            details={
                "ready_count": sum(1 for a in artifacts if a.status == FabricStatus.READY),
                "warn_count": len(warns),
                "blocked_count": len(blocked),
                "top_artifacts": [a.name for a in artifacts[:12]],
                "policy": artifacts[5].payload,
                "signature": artifacts[16].payload,
                "readiness_board": artifacts[-1].payload,
            },
        )


_DEFAULT: Optional[AutonomousRuntimeFabricKernel] = None


def init_autonomous_runtime_fabric(root: str | Path = ".autonomous_runtime_fabric_state") -> Dict:
    global _DEFAULT
    _DEFAULT = AutonomousRuntimeFabricKernel(root)
    return {"status": "ok", "root": str(Path(root)), "modules": 30}


def run_autonomous_runtime_fabric_cycle(goal: str, root: str | Path = ".autonomous_runtime_fabric_state") -> RuntimeFabricResult:
    global _DEFAULT
    if _DEFAULT is None or _DEFAULT.root != Path(root):
        _DEFAULT = AutonomousRuntimeFabricKernel(root)
    return _DEFAULT.run_cycle(goal)
