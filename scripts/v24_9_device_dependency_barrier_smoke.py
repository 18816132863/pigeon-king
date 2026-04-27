#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from execution.device_dependency_barrier import ActionState, DeviceDependencyBarrier

states = {
    "alarm": ActionState("alarm", "timeout_pending_verify"),
}
actions = [
    ActionState("notify", "queued", ["alarm"]),
    ActionState("local_summary", "queued", [], end_side=False),
]
barrier = DeviceDependencyBarrier()
result = barrier.classify_next(actions, states)
assert result["notify"].startswith("blocked_by_pending_verify")
assert result["local_summary"] == "ready"
print("v24_9_device_dependency_barrier_smoke: pass")
