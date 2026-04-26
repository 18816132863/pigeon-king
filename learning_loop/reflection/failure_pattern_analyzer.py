class FailurePatternAnalyzer:
    def analyze(self, events: list[dict]) -> dict:
        failures = [e for e in events if e.get("status") in {"failed", "timeout", "blocked"}]
        return {
            "status": "analyzed",
            "failure_count": len(failures),
            "patterns": ["permission_missing" if "permission" in str(failures) else "general_failure"] if failures else [],
        }
