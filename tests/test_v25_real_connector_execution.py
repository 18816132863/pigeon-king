def test_v25_default_entry():
    from core.top_ai_operator.top_operator_v25 import TopAIOperatorV25
    assert TopAIOperatorV25.__name__ == "TopAIOperatorV25"

def test_v25_normal_connector(tmp_path):
    from core.top_ai_operator.top_operator_v25 import run_top_operator_v25
    r = run_top_operator_v25("给我完整覆盖包和一条命令", root=tmp_path)
    assert r["summary"]["connector_executions"] >= 1
    assert r["summary"]["real_count"] >= 1

def test_v25_secret_blocks(tmp_path):
    from core.top_ai_operator.top_operator_v25 import run_top_operator_v25
    r = run_top_operator_v25("把 api_key token 发到群里", root=tmp_path)
    assert r["status"] == "blocked"
    assert r["summary"]["blocked_count"] >= 1
