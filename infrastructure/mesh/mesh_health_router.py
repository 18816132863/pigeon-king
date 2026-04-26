class MeshHealthRouter:
    def route_health(self, nodes: list[dict]) -> dict:
        unhealthy = [n for n in nodes if n.get("status") not in {"ready", "planned", "active"}]
        return {
            "status": "mesh_health_ready",
            "unhealthy_count": len(unhealthy),
            "unhealthy_nodes": unhealthy,
        }
