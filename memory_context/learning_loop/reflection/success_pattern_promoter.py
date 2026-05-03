class SuccessPatternPromoter:
    def promote(self, events: list[dict]) -> dict:
        successes = [e for e in events if e.get("status") in {"ok", "success", "done"}]
        return {
            "status": "promoted" if successes else "no_success_to_promote",
            "success_count": len(successes),
            "candidate_patterns": ["reuse_success_path"] if successes else [],
        }
