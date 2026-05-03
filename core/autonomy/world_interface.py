from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
from .schemas import ConnectorSpec, ConnectorKind, RiskLevel, new_id
from .storage import JsonStore


class WorldInterface:
    """V88: external world interface registry.

    It manages local tools, APIs, MCP-like connectors and device/app adapters.
    It does not execute arbitrary external code; it only registers, matches and
    gates access to capabilities.
    """

    def __init__(self, root: str | Path = ".autonomy_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "connectors.json")
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        data = self.store.read([])
        if data:
            return
        defaults = [
            ConnectorSpec(id="connector_file_search", name="File Search", kind=ConnectorKind.FILE, capabilities=["file_read", "document_search", "knowledge_lookup"], risk_level=RiskLevel.L1),
            ConnectorSpec(id="connector_web_research", name="Web Research", kind=ConnectorKind.API, capabilities=["web_search", "current_info", "fact_check"], risk_level=RiskLevel.L1, requires_approval=False),
            ConnectorSpec(id="connector_calendar", name="Calendar", kind=ConnectorKind.APP, capabilities=["calendar_read", "calendar_write", "schedule"], risk_level=RiskLevel.L3, requires_approval=True),
            ConnectorSpec(id="connector_email", name="Email", kind=ConnectorKind.APP, capabilities=["email_read", "email_draft", "email_send"], risk_level=RiskLevel.L4, requires_approval=True),
            ConnectorSpec(id="connector_local_shell", name="Local Shell", kind=ConnectorKind.LOCAL, capabilities=["script_run", "file_modify"], risk_level=RiskLevel.L4, requires_approval=True),
        ]
        self.store.write([self._to_dict(x) for x in defaults])

    def register(self, name: str, kind: ConnectorKind, capabilities: List[str], risk_level: RiskLevel = RiskLevel.L1, requires_approval: bool = False, metadata: Optional[Dict] = None) -> ConnectorSpec:
        data = self.store.read([])
        spec = ConnectorSpec(
            id=new_id("connector"),
            name=name,
            kind=kind,
            capabilities=sorted(set(capabilities)),
            risk_level=risk_level,
            requires_approval=requires_approval,
            metadata=metadata or {},
        )
        data.append(self._to_dict(spec))
        self.store.write(data)
        return spec

    def list_connectors(self, enabled_only: bool = True) -> List[ConnectorSpec]:
        out = [self._from_dict(x) for x in self.store.read([])]
        if enabled_only:
            out = [x for x in out if x.enabled]
        return out

    def match_capabilities(self, required: List[str]) -> List[ConnectorSpec]:
        required_set = set(required)
        matches = []
        for c in self.list_connectors():
            if required_set & set(c.capabilities):
                matches.append(c)
        matches.sort(key=lambda x: (x.requires_approval, x.risk_level.value, x.name))
        return matches

    def can_satisfy(self, required: List[str]) -> bool:
        have = set()
        for c in self.list_connectors():
            have.update(c.capabilities)
        return set(required).issubset(have)

    def _to_dict(self, spec: ConnectorSpec) -> Dict:
        return {
            "id": spec.id,
            "name": spec.name,
            "kind": spec.kind.value,
            "capabilities": spec.capabilities,
            "risk_level": spec.risk_level.value,
            "enabled": spec.enabled,
            "requires_approval": spec.requires_approval,
            "metadata": spec.metadata,
        }

    def _from_dict(self, item: Dict) -> ConnectorSpec:
        return ConnectorSpec(
            id=item["id"],
            name=item["name"],
            kind=ConnectorKind(item["kind"]),
            capabilities=list(item.get("capabilities", [])),
            risk_level=RiskLevel(item.get("risk_level", RiskLevel.L1.value)),
            enabled=bool(item.get("enabled", True)),
            requires_approval=bool(item.get("requires_approval", False)),
            metadata=dict(item.get("metadata", {})),
        )
