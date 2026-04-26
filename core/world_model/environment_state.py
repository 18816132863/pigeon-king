class EnvironmentState:
    def snapshot(self, connected: bool = False, authorized_connectors: list[str] | None = None) -> dict:
        return {
            "connected_runtime": connected,
            "authorized_connectors": authorized_connectors or [],
            "missing_authorizations": [] if authorized_connectors else ["external_connectors"],
        }
