"""Risk proof packages for autonomous pending-access runs."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping, Sequence

from governance.embodied_pending_state import CommitBarrier, assert_pending_access_frozen
from .operating_constitution import OperatingConstitution


@dataclass
class RiskProof:
    proof_id: str
    node_id: str
    semantic_class: str
    constitutional_decision: str
    barrier_mode: str
    freeze_ok: bool
    real_side_effect: bool
    obligations_satisfied: bool
    evidence: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RiskProofBuilder:
    def __init__(self) -> None:
        self.constitution = OperatingConstitution()
        self.barrier = CommitBarrier()

    def build_for_node(self, node: Mapping[str, Any], outcome: Mapping[str, Any] | None = None, index: int = 0) -> RiskProof:
        action = dict(node.get("action") or {})
        outcome = dict(outcome or {})
        constitution = self.constitution.evaluate(action)
        barrier = self.barrier.check(action)
        freeze = assert_pending_access_frozen()
        real_side_effect = bool(outcome.get("real_side_effect") is True or outcome.get("real_side_effects", 0))
        obligations_satisfied = (
            freeze.get("ok") is True
            and barrier.real_side_effect_allowed is False
            and constitution.allowed_to_execute_live is False
            and real_side_effect is False
        )
        evidence = {
            "constitution": constitution.to_dict(),
            "commit_barrier": barrier.to_dict(),
            "freeze_switch": freeze,
            "checkpoint_required": node.get("checkpoint_required") is True,
            "outcome_status": outcome.get("status"),
            "approval_packet_present": bool(outcome.get("approval_packet")),
        }
        return RiskProof(
            proof_id=f"risk_proof_{index:06d}",
            node_id=str(node.get("node_id") or f"node_{index:03d}"),
            semantic_class=barrier.semantic_class,
            constitutional_decision=constitution.constitutional_decision,
            barrier_mode=barrier.mode,
            freeze_ok=bool(freeze.get("ok")),
            real_side_effect=real_side_effect,
            obligations_satisfied=obligations_satisfied,
            evidence=evidence,
        )

    def build_for_run(self, run: Mapping[str, Any]) -> Dict[str, Any]:
        nodes = list((run.get("task_graph") or {}).get("nodes") or [])
        outcomes = list(run.get("node_outcomes") or [])
        proofs: List[Dict[str, Any]] = []
        for idx, node in enumerate(nodes, start=1):
            matching_outcome = outcomes[idx - 1].get("outcome", {}) if idx - 1 < len(outcomes) else {}
            proofs.append(self.build_for_node(node, matching_outcome, idx).to_dict())
        ok = bool(proofs) and all(p.get("obligations_satisfied") is True for p in proofs)
        return {
            "status": "pass" if ok else "fail",
            "proof_count": len(proofs),
            "all_obligations_satisfied": ok,
            "proofs": proofs,
        }


def build_risk_proofs(run: Mapping[str, Any]) -> Dict[str, Any]:
    return RiskProofBuilder().build_for_run(run)
