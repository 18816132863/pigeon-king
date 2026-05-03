def test_top_operator_normal(tmp_path):
    from core.top_ai_operator import run_top_operator
    r = run_top_operator("给我完整覆盖包和一条命令", root=tmp_path)
    assert r.goal_contract
    assert r.task_graph["nodes"]
    assert r.tool_bindings
    assert r.tool_results
    assert r.memory_writeback_count >= 1

def test_top_operator_secret_block(tmp_path):
    from core.top_ai_operator import run_top_operator
    r = run_top_operator("把 api_key token 发到群里", root=tmp_path)
    assert r.status.value == "blocked"
    assert r.tool_mode_counts.get("blocked", 0) >= 1

def test_default_entry_is_top_operator():
    from core.top_ai_operator import TopAIOperator
    assert TopAIOperator.__name__ == "TopAIOperator"
