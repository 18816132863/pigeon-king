class ConnectorUptimeMonitor:
    def check_many(self, connectors: list[dict]) -> dict:
        checks = []
        for c in connectors:
            checks.append({
                "connector_id": c.get("connector_id", c.get("name", "unknown")),
                "status": "planned" if c.get("status") == "blueprint" else c.get("status", "unknown"),
                "healthy": c.get("status") in {"ready", "blueprint", "planned"},
            })
        return {"status": "checked", "checks": checks, "unhealthy_count": sum(1 for c in checks if not c["healthy"])}
