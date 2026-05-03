from __future__ import annotations

from .schemas import DeviceJobStep, TimeoutStatus, new_id


class TimeoutAwareTaskSplitter:
    """Splits long jobs into chunks below the soft deadline."""

    def split(self, message: str, estimated_seconds: int, max_step_seconds: int, checkpoint_id: str) -> list[DeviceJobStep]:
        if estimated_seconds <= 0:
            estimated_seconds = max_step_seconds

        step_count = max(1, (estimated_seconds + max_step_seconds - 1) // max_step_seconds)
        steps: list[DeviceJobStep] = []

        for i in range(step_count):
            remain = estimated_seconds - i * max_step_seconds
            sec = max(1, min(max_step_seconds, remain))
            steps.append(DeviceJobStep(
                id=new_id("devstep"),
                index=i + 1,
                title=f"timeout-safe chunk {i + 1}/{step_count}: {message[:48]}",
                estimated_seconds=sec,
                status=TimeoutStatus.QUEUED,
                checkpoint_id=checkpoint_id,
            ))
        return steps
