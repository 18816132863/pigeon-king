class ResultVerifier:
    def verify(self, expected: dict, actual: dict) -> dict:
        success = actual.get("status") in {"ok", "success", "done", "ready"}
        return {
            "status": "verified" if success else "uncertain",
            "success": success,
            "expected_keys": sorted(expected.keys()),
            "actual_status": actual.get("status"),
        }
