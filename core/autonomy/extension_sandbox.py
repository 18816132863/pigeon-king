from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
from .schemas import ExtensionProposal, ExtensionStatus, RiskLevel, new_id
from .storage import JsonStore


class ExtensionSandbox:
    """V90: safe capability extension sandbox.

    This module deliberately does NOT install packages automatically.
    It creates proposals, simulates sandbox evaluation, requires scoring,
    and only promotes capabilities after evaluation passes.
    """

    def __init__(self, root: str | Path = ".autonomy_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "extension_proposals.json")

    def propose(self, capability_name: str, source_type: str = "trusted_catalog", source_ref: str = "", risk_level: RiskLevel = RiskLevel.L3) -> ExtensionProposal:
        data = self.store.read([])
        proposal = ExtensionProposal(
            id=new_id("ext"),
            capability_name=capability_name,
            source_type=source_type,
            source_ref=source_ref or f"catalog://{capability_name}",
            risk_level=risk_level,
            rollback_plan=f"disable capability {capability_name}; remove sandbox artifact; revert manifest entry",
            notes=["proposal_created"],
        )
        data.append(self._to_dict(proposal))
        self.store.write(data)
        return proposal

    def evaluate(self, proposal_id: str, checks: Optional[Dict[str, bool]] = None) -> ExtensionProposal:
        checks = checks or {
            "source_trusted": True,
            "has_rollback": True,
            "minimal_test_passed": True,
            "no_forbidden_permissions": True,
        }
        data = self.store.read([])
        for item in data:
            if item["id"] == proposal_id:
                score = sum(1 for v in checks.values() if v) / max(1, len(checks))
                item["evaluation_score"] = score
                item["status"] = ExtensionStatus.EVALUATED.value
                item.setdefault("notes", []).append(f"evaluated:{score:.2f}")
                if score >= 0.9:
                    item["status"] = ExtensionStatus.PROMOTED.value
                    item["promoted"] = True
                    item.setdefault("notes", []).append("promoted_to_available")
                else:
                    item["status"] = ExtensionStatus.REJECTED.value
                    item["promoted"] = False
                    item.setdefault("notes", []).append("rejected_by_sandbox")
                self.store.write(data)
                return self._from_dict(item)
        raise KeyError(f"unknown proposal_id: {proposal_id}")

    def list_proposals(self) -> List[ExtensionProposal]:
        return [self._from_dict(x) for x in self.store.read([])]

    def _to_dict(self, p: ExtensionProposal) -> Dict:
        return {
            "id": p.id,
            "capability_name": p.capability_name,
            "source_type": p.source_type,
            "source_ref": p.source_ref,
            "risk_level": p.risk_level.value,
            "status": p.status.value,
            "evaluation_score": p.evaluation_score,
            "promoted": p.promoted,
            "rollback_plan": p.rollback_plan,
            "notes": p.notes,
        }

    def _from_dict(self, item: Dict) -> ExtensionProposal:
        return ExtensionProposal(
            id=item["id"],
            capability_name=item["capability_name"],
            source_type=item.get("source_type", "trusted_catalog"),
            source_ref=item.get("source_ref", ""),
            risk_level=RiskLevel(item.get("risk_level", RiskLevel.L3.value)),
            status=ExtensionStatus(item.get("status", ExtensionStatus.PROPOSED.value)),
            evaluation_score=float(item.get("evaluation_score", 0.0)),
            promoted=bool(item.get("promoted", False)),
            rollback_plan=item.get("rollback_plan", ""),
            notes=list(item.get("notes", [])),
        )
