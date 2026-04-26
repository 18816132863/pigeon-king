class CapabilityRetirementPolicy:
    def evaluate(self, capability: dict) -> dict:
        failures = capability.get("failure_count", 0)
        unused_days = capability.get("unused_days", 0)
        retire = failures >= 5 or unused_days >= 90
        return {
            "status": "retire" if retire else "keep",
            "reason": "failure_or_unused" if retire else "still_useful",
            "requires_backup": retire,
        }
