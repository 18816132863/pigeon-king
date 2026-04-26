class ConnectorHealthMonitor:
    def check(self, connector: dict) -> dict:
        return {
            "connector_id": connector.get("connector_id"),
            "status": "not_authorized" if connector.get("requires_user_authorization") else "ready",
            "can_execute": False,
            "can_plan": True,
        }
