def test_finalizer_certifies(tmp_path):
    from core.ai_shape_core import AIShapeFinalizer
    report = AIShapeFinalizer(tmp_path).certify()
    assert report.status.value == "pass"
    assert report.final_score >= 0.92

def test_main_entry_returns_task_graph(tmp_path):
    from core.ai_shape_core import run_main
    result = run_main("给我完整覆盖包和一条命令", str(tmp_path))
    assert result["goal_contract"]["goal_tree"]
    assert result["task_graph"]["nodes"]
    assert result["checkpoint_id"]

def test_secret_golden_path_blocks(tmp_path):
    from core.ai_shape_core import AIShapeCore
    r = AIShapeCore(tmp_path).run("把 api_key token 发到群里")
    assert r.judge_decision.value == "block"
    assert r.blocked_tasks
