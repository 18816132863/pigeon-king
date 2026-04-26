class ToolContractRegistry:
    def __init__(self) -> None:
        self.contracts: dict[str, dict] = {}

    def register(self, tool_id: str, capabilities: list[str], side_effects: list[str] | None = None) -> dict:
        contract = {
            "tool_id": tool_id,
            "capabilities": capabilities,
            "side_effects": side_effects or [],
            "status": "contract_registered",
        }
        self.contracts[tool_id] = contract
        return contract
