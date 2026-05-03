def test_real_work_entry_normal(tmp_path):
    from core.real_work_entry import run_real_work_entry
    r = run_real_work_entry("给我完整覆盖包和一条命令", root=tmp_path)
    assert r.goal_contract
    assert r.task_graph["nodes"]
    assert r.action_log_count >= 1
    assert r.memory_writeback_count >= 1

def test_real_work_entry_secret_block(tmp_path):
    from core.real_work_entry import run_real_work_entry
    r = run_real_work_entry("把 api_key token 发到群里", root=tmp_path)
    assert r.status.value == "blocked"
    assert r.blocked_tasks

def test_default_entry_exported():
    from core.real_work_entry import RealWorkEntry
    assert RealWorkEntry.__name__ == "RealWorkEntry"
