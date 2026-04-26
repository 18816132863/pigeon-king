class RuntimeReplayEngine:
    def replay(self, traces: list[dict]) -> dict:
        return {
            "status": "replayed",
            "trace_count": len(traces),
            "failures": [t for t in traces if t.get("outcome", {}).get("status") in {"failed", "timeout"}],
        }
