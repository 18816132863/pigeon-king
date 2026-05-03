from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .schemas import ConnectorCandidate, TrustLevel, PermissionScope, new_id, dataclass_to_dict
from .storage import JsonStore


class ConnectorCatalog:
    """V99: connector marketplace/catalog governance."""

    def __init__(self, root: str | Path = ".operating_agent_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "connector_catalog.json")
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if self.store.read([]):
            return
        candidates = [
            ConnectorCandidate(new_id("conn"), "Local File Connector", "file_read", "builtin", TrustLevel.HIGH, 0.95, [PermissionScope.READ]),
            ConnectorCandidate(new_id("conn"), "Web Research Connector", "web_search", "builtin", TrustLevel.HIGH, 0.92, [PermissionScope.READ]),
            ConnectorCandidate(new_id("conn"), "Email Draft Connector", "email_draft", "builtin", TrustLevel.MEDIUM, 0.82, [PermissionScope.WRITE]),
            ConnectorCandidate(new_id("conn"), "Email Send Connector", "email_send", "builtin", TrustLevel.MEDIUM, 0.75, [PermissionScope.EXTERNAL_SEND]),
            ConnectorCandidate(new_id("conn"), "Plugin Installer Connector", "plugin_install", "sandbox", TrustLevel.LOW, 0.55, [PermissionScope.INSTALL]),
            ConnectorCandidate(new_id("conn"), "Device Control Connector", "device_control", "local", TrustLevel.MEDIUM, 0.70, [PermissionScope.DEVICE_CONTROL]),
        ]
        self.store.write([dataclass_to_dict(x) for x in candidates])

    def register(self, name: str, capability: str, source: str, trust_level: TrustLevel, score: float, permissions: List[PermissionScope] | None = None) -> ConnectorCandidate:
        data = self.store.read([])
        c = ConnectorCandidate(new_id("conn"), name, capability, source, trust_level, score, permissions or [])
        data.append(dataclass_to_dict(c))
        self.store.write(data)
        return c

    def search(self, capability: str, min_trust: TrustLevel = TrustLevel.LOW) -> List[ConnectorCandidate]:
        trust_order = {
            TrustLevel.UNKNOWN: 0,
            TrustLevel.LOW: 1,
            TrustLevel.MEDIUM: 2,
            TrustLevel.HIGH: 3,
            TrustLevel.OFFICIAL: 4,
        }
        threshold = trust_order[min_trust]
        out = []
        for item in self.store.read([]):
            c = self._from_dict(item)
            if c.capability == capability and trust_order[c.trust_level] >= threshold:
                out.append(c)
        out.sort(key=lambda x: (x.score, x.trust_level.value), reverse=True)
        return out

    def resolve_many(self, capabilities: List[str]) -> Dict[str, List[ConnectorCandidate]]:
        return {cap: self.search(cap) for cap in capabilities}

    def _from_dict(self, item: Dict) -> ConnectorCandidate:
        return ConnectorCandidate(
            id=item["id"],
            name=item["name"],
            capability=item["capability"],
            source=item["source"],
            trust_level=TrustLevel(item["trust_level"]),
            score=float(item.get("score", 0.0)),
            requires_permission=[PermissionScope(x) for x in item.get("requires_permission", [])],
            metadata=dict(item.get("metadata", {})),
        )
