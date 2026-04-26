class APIConnectorBlueprint:
    def build(self, name: str, scopes: list[str]) -> dict:
        return {
            "type": "api",
            "name": name,
            "scopes": scopes,
            "auth_required": True,
            "least_privilege": True,
            "status": "blueprint",
        }
