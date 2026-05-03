import time
import threading

from orchestration.workflow.workflow_engine import WorkflowEngine
from orchestration.workflow.state_machine import StepState


def _spec(name, steps):
    return {
        "workflow_id": name,
        "version": str(time.time_ns()),
        "name": name,
        "steps": steps,
        "max_retries": 0,
    }


def test_two_independent_safe_steps_run_in_parallel():
    engine = WorkflowEngine(max_parallel_steps=2)

    def handler(action, step_input):
        time.sleep(0.20)
        return {"action": action}

    engine.register_action_handler("safe_sleep", handler)
    spec = _spec("v86_parallel_basic", [
        {"step_id": "a", "name": "a", "action": "safe_sleep_a", "params": {"side_effect_type": "none"}},
        {"step_id": "b", "name": "b", "action": "safe_sleep_b", "params": {"side_effect_type": "none"}},
    ])

    started = time.perf_counter()
    result = engine.run_workflow(workflow_spec=spec, context_bundle={})
    elapsed = time.perf_counter() - started

    assert result.step_results["a"].status == StepState.COMPLETED
    assert result.step_results["b"].status == StepState.COMPLETED
    assert elapsed < 0.40


def test_max_parallel_steps_is_respected():
    engine = WorkflowEngine(max_parallel_steps=2)
    lock = threading.Lock()
    active = 0
    max_seen = 0

    def handler(action, step_input):
        nonlocal active, max_seen
        with lock:
            active += 1
            max_seen = max(max_seen, active)
        time.sleep(0.12)
        with lock:
            active -= 1
        return {"action": action}

    engine.register_action_handler("safe_job", handler)
    spec = _spec("v86_parallel_limit", [
        {"step_id": "a", "name": "a", "action": "safe_job_a", "params": {"side_effect_type": "none"}},
        {"step_id": "b", "name": "b", "action": "safe_job_b", "params": {"side_effect_type": "none"}},
        {"step_id": "c", "name": "c", "action": "safe_job_c", "params": {"side_effect_type": "none"}},
        {"step_id": "d", "name": "d", "action": "safe_job_d", "params": {"side_effect_type": "none"}},
    ])

    result = engine.run_workflow(workflow_spec=spec, context_bundle={})

    assert all(sr.status == StepState.COMPLETED for sr in result.step_results.values())
    assert max_seen <= 2
    assert max_seen == 2


def test_dependency_step_waits_for_parallel_dependencies():
    engine = WorkflowEngine(max_parallel_steps=2)
    timestamps = {}
    lock = threading.Lock()

    def handler(action, step_input):
        with lock:
            timestamps[action + ":start"] = time.perf_counter()
        if action != "safe_final":
            time.sleep(0.10)
        with lock:
            timestamps[action + ":end"] = time.perf_counter()
        return {"action": action}

    engine.register_action_handler("safe", handler)
    spec = _spec("v86_parallel_dependencies", [
        {"step_id": "a", "name": "a", "action": "safe_a", "params": {"side_effect_type": "none"}},
        {"step_id": "b", "name": "b", "action": "safe_b", "params": {"side_effect_type": "none"}},
        {"step_id": "final", "name": "final", "action": "safe_final", "depends_on": ["a", "b"], "params": {"side_effect_type": "none"}},
    ])

    result = engine.run_workflow(workflow_spec=spec, context_bundle={})

    assert result.step_results["final"].status == StepState.COMPLETED
    assert timestamps["safe_final:start"] >= timestamps["safe_a:end"]
    assert timestamps["safe_final:start"] >= timestamps["safe_b:end"]
