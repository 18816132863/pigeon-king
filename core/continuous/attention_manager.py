from __future__ import annotations


class AttentionManager:
    """Decide what deserves attention without spamming the user."""

    def rank(self, signals: list[dict]) -> dict:
        ranked = []
        for idx, signal in enumerate(signals):
            priority = signal.get("priority", "normal")
            score = {"urgent": 100, "high": 80, "normal": 50, "low": 20}.get(priority, 50)
            if signal.get("deadline"):
                score += 10
            ranked.append({**signal, "attention_score": score, "rank_id": idx})
        ranked.sort(key=lambda x: x["attention_score"], reverse=True)
        return {
            "status": "ranked",
            "top": ranked[:5],
            "should_interrupt_user": bool(ranked and ranked[0]["attention_score"] >= 90),
        }
