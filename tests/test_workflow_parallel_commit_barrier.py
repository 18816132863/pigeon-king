import time

from orchestration.workflow.workflow_engine import WorkflowEngine
from orchestration.workflow.state_machine import StepState
from orchestration.workflow.parallel_policy import ParallelClass, ParallelPolicy
from orchestration.workflow.workflow_registry import WorkflowStep


def test_payment_external_send_and_physical_actions_are_not_safe_parallel():
    policy = ParallelPolicy()
    steps = [
        WorkflowStep(step_id="pay", name="pay", action="payment_checkout"),
        WorkflowStep(step_id="send", name="send", action="send_email"),
        WorkflowStep(step_id="robot", name="robot", action="robot_actuate"),
        WorkflowStep(step_id="safe", name="safe", action="generate_report"),
    ]

    decisions = {s.step_id: policy.classify(s).parallel_class for s in steps}

    assert decisions["pay"] == ParallelClass.APPROVAL_REQUIRED
    assert decisions["send"] == ParallelClass.APPROVAL_REQUIRED
    assert decisions["robot"] == ParallelClass.APPROVAL_REQUIRED
    assert decisions["safe"] == ParallelClass.SAFE_PARALLEL


def test_commit_barrier_blocks_unapproved_payment_step():
    engine = WorkflowEngine(max_parallel_steps=2)
    called = []

    def handler(action, step_input):
        called.append(action)
        return {"action": action}

    engine.register_action_handler("payment", handler)
    spec = {
        "workflow_id": "v86_commit_barrier",
        "version": str(time.time_ns()),
        "name": "v86_commit_barrier",
        "steps": [
            {"step_id": "pay", "name": "pay", "action": "payment_checkout", "params": {"side_effect_type": "payment"}},
        ],
        "max_retries": 0,
    }

    result = engine.run_workflow(workflow_spec=spec, context_bundle={})

    assert result.step_results["pay"].status == StepState.SKIPPED
    assert "payment_checkout" not in called
    assert "Commit barrier" in (result.step_results["pay"].error or "")
