import time

def test_v26_default_entry():
    from core.device_timeout_resilience.operator_v26 import TopAIOperatorV26
    assert TopAIOperatorV26.__name__ == "TopAIOperatorV26"

def test_long_task_fast_ack(tmp_path):
    from core.device_timeout_resilience import run_top_operator_v26
    started = time.time()
    r = run_top_operator_v26("端侧 Calendar 读取大量日程，容易超过60秒", root=tmp_path, metadata={"estimated_seconds": 180})
    assert time.time() - started < 10
    assert r["summary"]["step_count"] >= 4
    assert r["summary"]["checkpoint"]
    assert r["summary"]["resumable"]

def test_device_approval_not_blocking(tmp_path):
    from core.device_timeout_resilience import run_top_operator_v26
    r = run_top_operator_v26("手机端操作设备，需要审批", root=tmp_path, metadata={"estimated_seconds": 120})
    assert r["status"] == "waiting_approval"
    assert r["summary"]["approval_required"]
