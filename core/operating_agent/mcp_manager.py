from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import time

from .schemas import MCPServerSpec, TrustLevel, new_id, dataclass_to_dict
from .storage import JsonStore


class MCPManager:
    """V100: remote MCP/server connector manager.

    This is a safe registry and handshake simulator; actual remote execution
    must be gated by PermissionVault and ConstitutionKernel.
    """

    def __init__(self, root: str | Path = ".operating_agent_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "mcp_servers.json")
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if self.store.read([]):
            return
        servers = [
            MCPServerSpec(new_id("mcp"), "Local Knowledge MCP", "mcp://local/knowledge", ["search", "read"], TrustLevel.HIGH),
            MCPServerSpec(new_id("mcp"), "Safe Web MCP", "mcp://safe/web", ["search", "fetch"], TrustLevel.MEDIUM),
        ]
        self.store.write([dataclass_to_dict(x) for x in servers])

    def register(self, name: str, endpoint: str, allowed_tools: List[str], trust_level: TrustLevel) -> MCPServerSpec:
        data = self.store.read([])
        spec = MCPServerSpec(new_id("mcp"), name, endpoint, allowed_tools, trust_level)
        data.append(dataclass_to_dict(spec))
        self.store.write(data)
        return spec

    def handshake(self, server_id: str) -> MCPServerSpec:
        data = self.store.read([])
        for item in data:
            if item["id"] == server_id:
                ok = item.get("enabled", True) and str(item.get("endpoint", "")).startswith("mcp://") and bool(item.get("allowed_tools"))
                item["handshake_ok"] = ok
                item["last_checked_at"] = time.time()
                self.store.write(data)
                return self._from_dict(item)
        raise KeyError(f"unknown server_id: {server_id}")

    def ready_servers(self) -> List[MCPServerSpec]:
        ready = []
        for item in self.store.read([]):
            spec = self._from_dict(item)
            if spec.enabled and spec.handshake_ok:
                ready.append(spec)
        return ready

    def handshake_all(self) -> List[MCPServerSpec]:
        ids = [item["id"] for item in self.store.read([])]
        return [self.handshake(i) for i in ids]

    def _from_dict(self, item: Dict) -> MCPServerSpec:
        return MCPServerSpec(
            id=item["id"],
            name=item["name"],
            endpoint=item["endpoint"],
            allowed_tools=list(item.get("allowed_tools", [])),
            trust_level=TrustLevel(item.get("trust_level", TrustLevel.UNKNOWN.value)),
            enabled=bool(item.get("enabled", True)),
            handshake_ok=bool(item.get("handshake_ok", False)),
            last_checked_at=item.get("last_checked_at"),
        )
