from __future__ import annotations

from .agent_role_registry import AgentRoleRegistry
from .delegation_planner import DelegationPlanner
from .collaboration_protocol import CollaborationProtocol
from .consensus_gate import ConsensusGate


class CollaborativeAutonomyKernel:
    """V10.7 internal multi-agent collaboration mesh."""

    def __init__(self) -> None:
        self.roles = AgentRoleRegistry()
        self.delegation = DelegationPlanner()
        self.protocol = CollaborationProtocol()
        self.consensus = ConsensusGate()

    def run(self, mission: dict) -> dict:
        roles = self.roles.list_roles()["roles"]
        delegated = self.delegation.delegate(mission, roles)
        protocol = self.protocol.apply(delegated)
        role_outputs = [{"role": t["role"], "status": "ok"} for t in delegated["tasks"]]
        consensus = self.consensus.decide(role_outputs)
        return {
            "status": "collaboration_ready",
            "shape": "Collaborative Autonomy Mesh",
            "roles": roles,
            "delegation": delegated,
            "protocol": protocol,
            "consensus": consensus,
            "side_effect": False,
        }
