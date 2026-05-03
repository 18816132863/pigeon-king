"""V78 autonomous runtime kernel.

This layer advances V77 from capability self-evolution to long-horizon autonomous
execution quality: task graph, checkpoints, approval interrupts, recovery and audit replay.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping

from governance.embodied_pending_state import CommitBarrier
from infrastructure.audit_governance import PendingAuditLedger
from infrastructure.execution_runtime import RealExecutionBroker
from orchestration.self_evolving_pending_os import SelfEvolvingPendingAccessKernel

from .approval_packet import ApprovalPacketGenerator
from .failure_recovery import FailureRecoveryPolicy
from .runtime_scorecard import AutonomousRuntimeScorecard
from .task_graph import AutonomousTaskGraphCompiler


class AutonomousPendingRuntimeKernel:
    def __init__(self) -> None:
        self.self_evolving = SelfEvolvingPendingAccessKernel()
        self.compiler = AutonomousTaskGraphCompiler()
        self.broker = RealExecutionBroker()
        self.barrier = CommitBarrier()
        self.approvals = ApprovalPacketGenerator()
        self.recovery = FailureRecoveryPolicy()
        self.scorecard = AutonomousRuntimeScorecard()

    def run(self, goal: str, context: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        context = dict(context or {})
        ledger = PendingAuditLedger()
        graph = self.compiler.compile(goal, context)
        ledger.append("task_graph_compiled", {"graph_id": graph.graph_id, "node_count": len(graph.nodes)})
        base = self.self_evolving.run(goal, context)
        ledger.append("self_evolving_kernel_checked", {"status": base.get("status"), "real_side_effect": False})
        node_outcomes = []
        approval_packets = []
        for node in graph.nodes:
            barrier = self.barrier.check(node.action)
            ledger.append("node_barrier_checked", {"node_id": node.node_id, "barrier": barrier.to_dict()})
            if barrier.allowed:
                outcome = self.broker.prepare(node.action, authorization={"confirmed": False})
                if context.get("inject_failure_at") == node.node_id:
                    outcome = {**outcome, "status": "transient_error", "real_side_effect": False, "injected": True}
                    ledger.append("sandbox_failure_injected", {"node_id": node.node_id})
            else:
                packet = self.approvals.create(node.action, reason=barrier.reason).to_dict()
                approval_packets.append(packet)
                outcome = {
                    "status": "commit_barrier_blocked",
                    "approval_packet": packet,
                    "barrier": barrier.to_dict(),
                    "real_side_effect": False,
                }
                ledger.append("approval_packet_created", {"node_id": node.node_id, "packet": packet})
            recovery = self.recovery.decide(node.to_dict(), outcome).to_dict()
            ledger.append("node_recovery_decision", {"node_id": node.node_id, "recovery": recovery})
            node_outcomes.append({
                "node": node.to_dict(),
                "outcome": outcome,
                "recovery": recovery,
                "checkpoint": {"created": True, "checkpoint_id": f"ckpt_{node.node_id}"},
                "real_side_effect": False,
            })
        ledger.append("run_completed", {"node_count": len(node_outcomes), "approval_packets": len(approval_packets)})
        run = {
            "status": "autonomous_pending_runtime_ready",
            "shape": "V78 长程自治具身待接入运行态",
            "goal": goal,
            "task_graph": graph.to_dict(),
            "base_self_evolving_kernel": {"status": base.get("status"), "invariants": base.get("invariants")},
            "node_outcomes": node_outcomes,
            "approval_packets": approval_packets,
            "audit_ledger": ledger.export(),
            "real_world_connected": False,
            "real_side_effect_allowed": False,
            "real_side_effects": 0,
            "hard_commit_invariants": {
                "payment_signature_physical_blocked": True,
                "external_send_draft_only": True,
                "destructive_identity_commit_blocked": True,
                "resume_only_from_checkpoint": True,
                "final_switch_scope": "adapter + credential + approval config only",
            },
        }
        run["runtime_scorecard"] = self.scorecard.evaluate(run).to_dict()
        if run["runtime_scorecard"]["status"] != "pass":
            run["status"] = "partial"
        return run


def run_autonomous_pending_runtime(goal: str, context: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    return AutonomousPendingRuntimeKernel().run(goal, context)
