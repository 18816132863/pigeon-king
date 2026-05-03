class EvaluationMemory:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def add(self, evaluation: dict) -> dict:
        self.records.append(evaluation)
        return {"status": "stored", "count": len(self.records)}

    def summary(self) -> dict:
        return {"total": len(self.records), "successful": sum(1 for r in self.records if r.get("success"))}
