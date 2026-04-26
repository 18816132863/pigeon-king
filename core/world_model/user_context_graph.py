class UserContextGraph:
    def build(self, facts: list[dict]) -> dict:
        return {
            "status": "graph_ready",
            "nodes": facts,
            "edges": [],
            "privacy": "local_only",
            "no_external_share": True,
        }
