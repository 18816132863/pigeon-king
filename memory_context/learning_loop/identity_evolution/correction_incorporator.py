class CorrectionIncorporator:
    def incorporate(self, model: dict, correction: dict) -> dict:
        updated = dict(model)
        updated.setdefault("corrections", []).append(correction)
        updated["last_correction_type"] = correction.get("type", "general")
        return {"status": "incorporated", "model": updated}
