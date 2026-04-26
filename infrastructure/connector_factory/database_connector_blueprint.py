class DatabaseConnectorBlueprint:
    def build(self, name: str, readonly: bool = True) -> dict:
        return {
            "type": "database",
            "name": name,
            "readonly": readonly,
            "write_requires_approval": not readonly,
            "status": "blueprint",
        }
