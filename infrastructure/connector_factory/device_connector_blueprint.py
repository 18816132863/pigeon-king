class DeviceConnectorBlueprint:
    def build(self, name: str, actions: list[str]) -> dict:
        high = [a for a in actions if a in {"send", "delete", "call", "payment", "account"}]
        return {
            "type": "device",
            "name": name,
            "actions": actions,
            "high_risk_actions": high,
            "strong_confirm_required": bool(high),
            "status": "blueprint",
        }
