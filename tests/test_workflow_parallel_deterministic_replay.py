import time

from orchestration.workflow.workflow_engine import WorkflowEngine
from orchestration.workflow.state_machine import StepState


def test_parallel_result_writeback_order_is_deterministic():
    engine = WorkflowEngine(max_parallel_steps=2)

    def handler(action, step_input):
        if action.endswith("a"):
            time.sleep(0.15)
        else:
            time.sleep(0.02)
        return {"action": action}

    engine.register_action_handler("safe", handler)
    spec = {
        "workflow_id": "v86_deterministic_replay",
        "version": str(time.time_ns()),
        "name": "v86_deterministic_replay",
        "steps": [
            {"step_id": "a", "name": "a", "action": "safe_a", "params": {"side_effect_type": "none"}},
            {"step_id": "b", "name": "b", "action": "safe_b", "params": {"side_effect_type": "none"}},
        ],
        "max_retries": 0,
    }

    result = engine.run_workflow(workflow_spec=spec, context_bundle={})

    assert result.step_results["a"].status == StepState.COMPLETED
    assert result.step_results["b"].status == StepState.COMPLETED
    assert list(result.step_results.keys()) == ["a", "b"]
