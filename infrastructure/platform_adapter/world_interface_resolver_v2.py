"""
V25.5 World Interface Resolver V2

Classifies available world interfaces without turning every integration into an
ad-hoc adapter. Supports local capability, device, connector, MCP-like and file/API
resources under one searchable catalog.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class WorldInterface:
    name: str
    kind: str  # local, device, connector, mcp, file, api
    trust_level: str  # builtin, trusted, review_required, blocked
    capabilities: List[str]


class WorldInterfaceResolverV2:
    def __init__(self) -> None:
        self._items: Dict[str, WorldInterface] = {}

    def register(self, item: WorldInterface) -> None:
        if item.trust_level == "blocked":
            raise ValueError(f"blocked interface cannot be registered active: {item.name}")
        self._items[item.name] = item

    def resolve(self, capability: str) -> List[WorldInterface]:
        return [
            item for item in self._items.values()
            if capability in item.capabilities and item.trust_level in {"builtin", "trusted", "review_required"}
        ]

    def has_capability(self, capability: str) -> bool:
        return bool(self.resolve(capability))
