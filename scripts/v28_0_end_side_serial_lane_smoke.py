from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestration.end_side_serial_lanes_v3 import EndSideSerialLaneV3, DeviceAction, make_idempotency_key
lane = EndSideSerialLaneV3()
actions = [
    DeviceAction("a1", "alarm", {"t": 1}, make_idempotency_key("alarm", {"t": 1})),
    DeviceAction("a2", "calendar", {"t": 2}, make_idempotency_key("calendar", {"t": 2}), depends_on=["a1"]),
]
receipts = lane.submit_many(actions, lambda a: {"status": "success"})
assert [r.status for r in receipts] == ["success", "success"]
dupe = lane.submit_many([actions[0]], lambda a: {"status": "success"})[0]
assert dupe.status == "skipped_duplicate"
print("v28_0_end_side_serial_lane_smoke: pass")
