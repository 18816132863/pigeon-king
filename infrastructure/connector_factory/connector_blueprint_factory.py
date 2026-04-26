from __future__ import annotations

from .api_connector_blueprint import APIConnectorBlueprint
from .mcp_connector_blueprint import MCPConnectorBlueprint
from .device_connector_blueprint import DeviceConnectorBlueprint
from .database_connector_blueprint import DatabaseConnectorBlueprint


class ConnectorBlueprintFactory:
    def build_all_domain_blueprints(self) -> list[dict]:
        return [
            APIConnectorBlueprint().build("generic_api", ["read", "search"]),
            MCPConnectorBlueprint().build("generic_mcp", ["search", "read", "plan"]),
            DeviceConnectorBlueprint().build("xiaoyi_device", ["read", "probe"]),
            DatabaseConnectorBlueprint().build("local_memory_db", readonly=True),
        ]
