class MeshNodeRegistry:
    def __init__(self) -> None:
        self.nodes: dict[str, dict] = {}

    def register(self, node_id: str, node_type: str, capabilities: list[str]) -> dict:
        node = {"node_id": node_id, "node_type": node_type, "capabilities": capabilities, "status": "planned"}
        self.nodes[node_id] = node
        return node

    def list_nodes(self) -> list[dict]:
        return list(self.nodes.values())
