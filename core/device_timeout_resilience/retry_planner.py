from __future__ import annotations


class RetryPlanner:
    """Retry/backoff planner for device connector tasks."""

    def plan(self, max_retries: int) -> dict:
        delays = []
        base = 2
        for i in range(max_retries):
            delays.append(base ** i)
        return {
            "max_retries": max_retries,
            "backoff_seconds": delays,
            "on_timeout": [
                "write checkpoint before hard timeout",
                "mark current step resumable",
                "return fast status to caller",
                "resume from next poll or approval",
            ],
            "on_repeated_failure": [
                "degrade to draft/dry-run",
                "keep evidence bundle",
                "ask for manual intervention",
            ],
        }
