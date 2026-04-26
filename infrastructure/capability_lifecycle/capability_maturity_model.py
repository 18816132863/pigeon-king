class CapabilityMaturityModel:
    STAGES = ["candidate", "sandbox", "experimental", "trusted", "core"]

    def classify(self, capability: dict) -> dict:
        evidence = capability.get("evidence_count", 0)
        if evidence >= 20 and capability.get("rollback_verified"):
            stage = "trusted"
        elif evidence >= 5:
            stage = "experimental"
        elif capability.get("sandboxed"):
            stage = "sandbox"
        else:
            stage = "candidate"
        return {"status": "classified", "stage": stage}
