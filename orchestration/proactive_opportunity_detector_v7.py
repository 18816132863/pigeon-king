"""V72.0 Bounded proactive opportunity detector."""
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Opportunity:
    opportunity_id: str
    title: str
    benefit: int
    risk: int
    requires_external_write: bool = False
    suggested_next_step: str = "draft_plan"

class ProactiveOpportunityDetector:
    layer = "L3_ORCHESTRATION"

    def filter_actionable(self, opportunities: List[Opportunity], max_risk: int = 2) -> List[Opportunity]:
        return [o for o in opportunities if o.risk <= max_risk and not o.requires_external_write]

    def propose(self, opportunities: List[Opportunity]) -> Dict[str, object]:
        actionable = sorted(self.filter_actionable(opportunities), key=lambda o: (-o.benefit, o.risk, o.opportunity_id))
        return {
            "mode": "propose_not_execute",
            "count": len(actionable),
            "top": actionable[0].opportunity_id if actionable else None,
            "requires_user_confirmation_for_execution": True,
        }
