"""Mock-first world interface contract registry.

Live adapters are represented as contracts, but the pending-access state only
executes their mock/sandbox side. This preserves the 'one final switch away'
shape without connecting real accounts, devices or payment rails.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional


@dataclass
class WorldAdapterContract:
    name: str
    kind: str  # local, connector, mcp, api, device, robot, payment, external_comm
    semantic_classes: List[str]
    mock_adapter_present: bool = True
    live_adapter_declared: bool = True
    live_enabled: bool = False
    credential_required: bool = True
    credential_bound: bool = False
    approval_required: bool = True
    audit_required: bool = True
    rollback_supported: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def ready_as_pending_contract(self) -> bool:
        return self.mock_adapter_present and self.live_adapter_declared and self.audit_required

    @property
    def live_connectable_now(self) -> bool:
        return self.live_enabled and self.credential_bound and self.approval_required


class MockContractRegistry:
    def __init__(self) -> None:
        self._contracts: Dict[str, WorldAdapterContract] = {}

    def register(self, contract: WorldAdapterContract) -> None:
        self._contracts[contract.name] = contract

    def get(self, name: str) -> Optional[WorldAdapterContract]:
        return self._contracts.get(name)

    def list_contracts(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self._contracts.values()]

    def coverage_report(self) -> Dict[str, Any]:
        total = len(self._contracts)
        pending_ready = sum(1 for c in self._contracts.values() if c.ready_as_pending_contract)
        live_now = sum(1 for c in self._contracts.values() if c.live_connectable_now)
        return {
            "status": "pass" if total and live_now == 0 and pending_ready == total else "partial",
            "total_contracts": total,
            "pending_ready_contracts": pending_ready,
            "live_connectable_now": live_now,
            "mock_coverage": round(pending_ready / total, 4) if total else 0.0,
            "policy": "mock_first_live_switch_closed",
            "contracts": self.list_contracts(),
        }


def build_default_contract_registry() -> MockContractRegistry:
    registry = MockContractRegistry()
    defaults = [
        WorldAdapterContract("file_read", "local", ["observe"], credential_required=False, approval_required=False, rollback_supported=False),
        WorldAdapterContract("knowledge_search", "local", ["observe", "reason"], credential_required=False, approval_required=False),
        WorldAdapterContract("draft_generator", "local", ["generate", "prepare"], credential_required=False, approval_required=False, rollback_supported=True),
        WorldAdapterContract("calendar_mock", "connector", ["prepare", "external_send"], rollback_supported=True, notes="create/update event only as draft or mock"),
        WorldAdapterContract("message_outbox_mock", "connector", ["prepare", "external_send"], rollback_supported=True, notes="draft/outbox only; no real send"),
        WorldAdapterContract("email_outbox_mock", "connector", ["prepare", "external_send"], rollback_supported=True, notes="draft only; live send disabled"),
        WorldAdapterContract("payment_mock", "payment", ["prepare", "payment"], rollback_supported=False, notes="checkout/payment hard-stopped"),
        WorldAdapterContract("contract_signature_mock", "api", ["prepare", "signature"], rollback_supported=False, notes="signature hard-stopped"),
        WorldAdapterContract("device_control_mock", "device", ["simulate", "physical_actuation"], rollback_supported=False, notes="device actuation mock only"),
        WorldAdapterContract("robot_controller_mock", "robot", ["simulate", "physical_actuation"], rollback_supported=False, notes="trajectory generation only"),
        WorldAdapterContract("identity_commit_mock", "api", ["prepare", "identity_commit"], rollback_supported=False, notes="identity commitments hard-stopped"),
        WorldAdapterContract("destructive_admin_mock", "api", ["prepare", "destructive"], rollback_supported=False, notes="destructive actions hard-stopped"),
        WorldAdapterContract("mcp_remote_tool_mock", "mcp", ["observe", "reason", "prepare", "external_send"], rollback_supported=True, notes="remote MCP contract declared; live call disabled by barrier"),
        WorldAdapterContract("world_model_sim", "local", ["simulate"], credential_required=False, approval_required=False, rollback_supported=True),
    ]
    for item in defaults:
        registry.register(item)
    return registry
