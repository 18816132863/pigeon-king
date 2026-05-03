class DecisionTraceIndex:
    def __init__(self) -> None:
        self.traces: list[dict] = []

    def add(self, trace: dict) -> dict:
        self.traces.append(trace)
        return {"status": "indexed", "count": len(self.traces)}

    def find_similar(self, action_type: str) -> list[dict]:
        return [t for t in self.traces if t.get("action_type") == action_type]
