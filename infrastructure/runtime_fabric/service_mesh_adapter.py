class ServiceMeshAdapter:
    def build_plan(self, services: list[dict]) -> dict:
        return {
            "status": "mesh_plan_ready",
            "services": services,
            "external_calls": 0,
            "requires_runtime_binding": True,
        }
