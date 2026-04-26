class MeshMessageBus:
    """Local message bus contract. No external sending."""

    def route(self, source: str, target: str, message: dict) -> dict:
        return {
            "status": "routed_locally",
            "source": source,
            "target": target,
            "message": message,
            "external_side_effect": False,
        }
