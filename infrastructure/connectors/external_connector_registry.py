from __future__ import annotations


class ExternalConnectorRegistry:
    """Registry contract for API/device/MCP/database/automation connectors."""

    def __init__(self) -> None:
        self.connectors: dict[str, dict] = {}

    def register_planned(self, connector_id: str, connector_type: str, scopes: list[str]) -> dict:
        self.connectors[connector_id] = {
            "connector_id": connector_id,
            "type": connector_type,
            "scopes": scopes,
            "status": "planned",
            "requires_user_authorization": True,
        }
        return self.connectors[connector_id]

    def list_connectors(self) -> list[dict]:
        return list(self.connectors.values())
