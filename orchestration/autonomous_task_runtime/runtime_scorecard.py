"""Runtime quality scorecard for V78 autonomous pending-access maturity."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping


@dataclass
class RuntimeScorecardResult:
    status: str
    score: float
    checks: Dict[str, bool]
    readiness_level: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AutonomousRuntimeScorecard:
    def evaluate(self, run: Mapping[str, Any]) -> RuntimeScorecardResult:
        ledger = run.get("audit_ledger") or {}
        graph = run.get("task_graph") or {}
        nodes = graph.get("nodes") or []
        outcomes = run.get("node_outcomes") or []
        approval_packets = run.get("approval_packets") or []
        checks = {
            "task_graph_exists": bool(nodes),
            "every_node_has_checkpoint": all(n.get("checkpoint_required") is True for n in nodes),
            "commit_nodes_have_approval_packets": sum(1 for n in nodes if (n.get("semantic") or {}).get("is_commit_action") is True) == len(approval_packets),
            "no_real_side_effects": ledger.get("real_side_effects", 1) == 0 and run.get("real_side_effects", 1) == 0,
            "audit_replayable": ledger.get("replayable") is True and ledger.get("event_count", 0) >= len(nodes),
            "failures_recovered_or_paused": all(o.get("recovery", {}).get("recovered") is True or o.get("recovery", {}).get("requires_user") is True for o in outcomes),
            "payment_signature_physical_blocked": run.get("hard_commit_invariants", {}).get("payment_signature_physical_blocked") is True,
            "external_send_draft_only": run.get("hard_commit_invariants", {}).get("external_send_draft_only") is True,
        }
        score = round(sum(1 for ok in checks.values() if ok) / max(len(checks), 1), 4)
        status = "pass" if score >= 1.0 else "partial"
        return RuntimeScorecardResult(status, score, checks, "V78_autonomous_pending_runtime_ready" if status == "pass" else "needs_more_runtime_hardening")
