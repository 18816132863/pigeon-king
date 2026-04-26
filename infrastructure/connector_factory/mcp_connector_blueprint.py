class MCPConnectorBlueprint:
    def build(self, name: str, tools: list[str]) -> dict:
        return {
            "type": "mcp",
            "name": name,
            "tools": tools,
            "sandbox_first": True,
            "status": "blueprint",
        }
