from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .schemas import (
    OperatingCycleResult,
    DecisionStatus,
    PermissionScope,
    ReleaseStage,
    new_id,
)
from .constitution_kernel import ConstitutionKernel
from .permission_vault import PermissionVault
from .connector_catalog import ConnectorCatalog
from .mcp_manager import MCPManager
from .plugin_sandbox import PluginSandboxManager
from .specialist_handoff import SpecialistHandoffManager
from .multi_agent_coordinator import MultiAgentCoordinator
from .recovery_ledger import RecoveryLedger
from .evaluation_benchmark import EvaluationBenchmark
from .release_governor import ReleaseGovernor


class OperatingAgentOrchestrator:
    """V97-V106 top-level governance orchestrator."""

    def __init__(self, root: str | Path = ".operating_agent_state"):
        self.root = Path(root)
        self.constitution = ConstitutionKernel(self.root)
        self.permissions = PermissionVault(self.root)
        self.connectors = ConnectorCatalog(self.root)
        self.mcp = MCPManager(self.root)
        self.sandbox = PluginSandboxManager(self.root)
        self.handoff = SpecialistHandoffManager(self.root)
        self.multi_agent = MultiAgentCoordinator(self.root)
        self.recovery = RecoveryLedger(self.root)
        self.benchmark = EvaluationBenchmark(self.root)
        self.release = ReleaseGovernor(self.root)

    def _infer_capabilities(self, goal: str) -> list[str]:
        caps = ["planning"]
        if any(x in goal for x in ["查", "最新", "规则", "政策"]):
            caps.append("web_search")
        if any(x in goal for x in ["文件", "文档", "压缩包"]):
            caps.append("file_read")
        if any(x in goal for x in ["邮件", "发给客户", "外部发送"]):
            caps.append("email_send")
        if any(x in goal for x in ["安装", "插件", "扩展"]):
            caps.append("plugin_install")
        if any(x in goal for x in ["设备", "手机", "电脑控制"]):
            caps.append("device_control")
        return sorted(set(caps))

    def run_cycle(self, goal: str, subject: str = "user", context: Optional[Dict] = None) -> OperatingCycleResult:
        context = context or {}
        run_id = new_id("oprun")

        decision = self.constitution.evaluate(goal)
        permissions_ok = self.permissions.check(subject, decision.required_permissions)

        # Read-only/default permissions are allowed implicitly.
        if not decision.required_permissions:
            permissions_ok = True

        required_caps = self._infer_capabilities(goal)
        connector_matches = self.connectors.resolve_many(required_caps)
        connector_count = sum(len(v) for v in connector_matches.values())

        mcp_ready = self.mcp.handshake_all()
        mcp_ready_count = len([x for x in mcp_ready if x.handshake_ok])

        sandbox_report = self.sandbox.evaluate_source(
            plugin_name="safe_planning_adapter",
            source_ref="builtin://safe_planning_adapter",
            source_text="def run(goal): return {'plan': goal}",
            has_rollback=True,
            test_passed=True,
        )

        consensus = self.multi_agent.coordinate(goal)
        handoff_agent = consensus["handoff_agents"][0] if consensus["handoff_agents"] else "none"

        self.recovery.record_checkpoint(
            run_id=run_id,
            action="governed_operating_cycle",
            checkpoint={
                "goal": goal,
                "constitution": decision.status.value,
                "required_caps": required_caps,
                "connectors": connector_count,
                "handoff_agent": handoff_agent,
            },
            rollback_plan="restore previous checkpoint; discard unapproved external actions",
            reversible=True,
        )
        recovery_entries = len(self.recovery.list_run(run_id))

        benchmark_results = self.benchmark.run(self.constitution)
        benchmark_score = self.benchmark.aggregate_score(benchmark_results)

        release = self.release.evaluate_release(
            constitution_ok=decision.status != DecisionStatus.BLOCK,
            permissions_ok=permissions_ok or decision.status == DecisionStatus.APPROVAL_REQUIRED,
            sandbox_ok=sandbox_report.promoted,
            benchmark_score=benchmark_score,
            recovery_ok=recovery_entries > 0,
            mcp_ok=mcp_ready_count > 0,
        )

        if decision.status == DecisionStatus.BLOCK:
            final_status = "blocked_by_constitution"
            next_action = "拒绝执行，并提示用户换成安全目标"
        elif decision.status == DecisionStatus.APPROVAL_REQUIRED and not permissions_ok:
            final_status = "waiting_permission_or_approval"
            next_action = "等待用户授权对应权限后继续"
        elif release.stage == ReleaseStage.BLOCKED:
            final_status = "blocked_by_release_gate"
            next_action = "修复 release gate blocker 后再推进"
        else:
            final_status = "ready_for_execution"
            next_action = "可交给 V86/V87-V96 执行图继续实际执行"

        return OperatingCycleResult(
            run_id=run_id,
            goal=goal,
            constitution_status=decision.status,
            permissions_ok=permissions_ok,
            connector_count=connector_count,
            mcp_ready_count=mcp_ready_count,
            sandbox_promoted=sandbox_report.promoted,
            handoff_agent=handoff_agent,
            recovery_entries=recovery_entries,
            benchmark_score=benchmark_score,
            release_stage=release.stage,
            final_status=final_status,
            next_action=next_action,
            details={
                "matched_rules": decision.matched_rules,
                "required_permissions": [p.value for p in decision.required_permissions],
                "required_capabilities": required_caps,
                "release_blockers": release.blockers,
                "consensus_domains": consensus["domains"],
            },
        )


_DEFAULT: Optional[OperatingAgentOrchestrator] = None


def init_operating_agent(root: str | Path = ".operating_agent_state") -> Dict:
    global _DEFAULT
    _DEFAULT = OperatingAgentOrchestrator(root)
    return {
        "status": "ok",
        "root": str(Path(root)),
        "rules": len(_DEFAULT.constitution.list_rules()),
        "mcp_servers": len(_DEFAULT.mcp.handshake_all()),
    }


def run_operating_cycle(goal: str, subject: str = "user", context: Optional[Dict] = None, root: str | Path = ".operating_agent_state") -> OperatingCycleResult:
    global _DEFAULT
    if _DEFAULT is None or _DEFAULT.root != Path(root):
        _DEFAULT = OperatingAgentOrchestrator(root)
    return _DEFAULT.run_cycle(goal, subject=subject, context=context)
