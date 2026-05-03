from __future__ import annotations

from typing import Dict
from .schemas import RuntimeReport, ReleaseStatus, new_id


class RuntimeReporter:
    """V135: final runtime status report."""

    def build(self, release_id: str, checks: Dict[str, str]) -> RuntimeReport:
        values = list(checks.values())
        failures = [x for x in values if x in {"fail", "blocked", "closed"}]
        warns = [x for x in values if x in {"warn", "degraded_ready"}]
        score = round((len(values) - len(failures) - 0.5 * len(warns)) / max(1, len(values)), 4)

        if failures:
            status = ReleaseStatus.BLOCKED
        elif warns:
            status = ReleaseStatus.DEGRADED_READY
        else:
            status = ReleaseStatus.READY

        summary = f"status={status.value}, score={score}, checks={len(values)}, failures={len(failures)}, warnings={len(warns)}"
        return RuntimeReport(
            id=new_id("runtime_report"),
            release_id=release_id,
            status=status,
            checks=checks,
            score=score,
            summary=summary,
        )
