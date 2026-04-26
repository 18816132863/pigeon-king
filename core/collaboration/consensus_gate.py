class ConsensusGate:
    """Gate role outputs before execution."""

    def decide(self, role_outputs: list[dict]) -> dict:
        blockers = []
        for item in role_outputs:
            if item.get("status") in {"blocked", "unsafe", "contradiction"}:
                blockers.append(item)
        return {
            "status": "blocked" if blockers else "consensus_ready",
            "blockers": blockers,
            "requires_user_review": bool(blockers),
        }
