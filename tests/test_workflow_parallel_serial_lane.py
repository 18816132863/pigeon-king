import time
import threading

from orchestration.workflow.workflow_engine import WorkflowEngine
from orchestration.workflow.state_machine import StepState


def test_two_end_side_like_actions_do_not_run_in_parallel():
    engine = WorkflowEngine(max_parallel_steps=4)
    lock = threading.Lock()
    active = 0
    max_seen = 0

    def handler(action, step_input):
        nonlocal active, max_seen
        with lock:
            active += 1
            max_seen = max(max_seen, active)
        time.sleep(0.10)
        with lock:
            active -= 1
        return {"action": action}

    engine.register_action_handler("calendar", handler)
    spec = {
        "workflow_id": "v86_serial_lane",
        "version": str(time.time_ns()),
        "name": "v86_serial_lane",
        "steps": [
            {"step_id": "cal_a", "name": "cal_a", "action": "calendar_create_event", "params": {"side_effect_type": "calendar_write"}},
            {"step_id": "cal_b", "name": "cal_b", "action": "calendar_create_event", "params": {"side_effect_type": "calendar_write"}},
        ],
        "max_retries": 0,
    }

    result = engine.run_workflow(workflow_spec=spec, context_bundle={})

    assert result.step_results["cal_a"].status == StepState.COMPLETED
    assert result.step_results["cal_b"].status == StepState.COMPLETED
    assert max_seen == 1
