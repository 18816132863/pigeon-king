from pathlib import Path


def test_v87_memory_kernel(tmp_path: Path):
    from core.autonomy import MemoryKernel
    from core.autonomy.schemas import MemoryKind

    m = MemoryKernel(tmp_path)
    m.remember_preference("update_style", "direct_package_first")
    assert m.get(MemoryKind.PREFERENCE, "update_style").value == "direct_package_first"
    assert m.search("direct_package_first")


def test_v88_world_interface(tmp_path: Path):
    from core.autonomy import WorldInterface

    w = WorldInterface(tmp_path)
    matches = w.match_capabilities(["web_search"])
    assert matches
    assert w.can_satisfy(["file_read", "document_search"])


def test_v89_capability_gap():
    from core.autonomy import CapabilityGapAnalyzer
    from core.autonomy.schemas import CapabilityGapStatus

    gap = CapabilityGapAnalyzer().analyze("给客户发送邮件", connector_capabilities=["email_send"])
    assert gap.status in {CapabilityGapStatus.CAN_USE_CONNECTOR, CapabilityGapStatus.NEED_HUMAN}


def test_v90_extension_sandbox(tmp_path: Path):
    from core.autonomy import ExtensionSandbox

    s = ExtensionSandbox(tmp_path)
    p = s.propose("new_safe_connector")
    e = s.evaluate(p.id)
    assert e.promoted is True


def test_v91_approval_interrupt(tmp_path: Path):
    from core.autonomy import ApprovalInterruptManager
    from core.autonomy.schemas import RiskLevel, ApprovalStatus

    a = ApprovalInterruptManager(tmp_path)
    t = a.create_ticket("send email", "send external message", RiskLevel.L4)
    assert t.status == ApprovalStatus.PENDING
    done = a.resolve(t.id, approve=True)
    assert done.status == ApprovalStatus.APPROVED


def test_v92_trace_audit(tmp_path: Path):
    from core.autonomy import TraceAudit

    t = TraceAudit(tmp_path)
    t.record("run1", "start", "started")
    assert t.summarize("run1")["events"] == 1


def test_v93_quality_evaluator(tmp_path: Path):
    from core.autonomy import QualityEvaluator

    q = QualityEvaluator(tmp_path).evaluate("run1", "goal", {"has_plan": True, "has_next_action": True, "actionable": True, "steps": 3})
    assert q.passed
    assert q.final_score >= 0.75


def test_v94_strategy_evolver(tmp_path: Path):
    from core.autonomy import StrategyEvolver, QualityEvaluator

    q = QualityEvaluator(tmp_path).evaluate("run1", "goal", {"has_plan": False, "has_next_action": False, "actionable": False, "steps": 20}, risk_blocked=True)
    changed = StrategyEvolver(tmp_path).evolve_from_quality(q)
    assert changed


def test_v95_continuous_task_runner(tmp_path: Path):
    from core.autonomy import ContinuousTaskRunner
    from core.autonomy.schemas import TaskRunStatus

    r = ContinuousTaskRunner(tmp_path)
    task = r.create("daily review", "review tasks", "daily")
    assert r.due()
    r.mark_run(task.id, TaskRunStatus.COMPLETED)
    assert not r.due()


def test_v96_autonomy_orchestrator(tmp_path: Path):
    from core.autonomy import run_autonomy_cycle
    from core.autonomy.schemas import ApprovalStatus

    safe = run_autonomy_cycle("整理今天计划", root=tmp_path)
    assert safe.run_id
    assert safe.memory_updates >= 1
    risky = run_autonomy_cycle("给客户发送邮件前先等我确认", root=tmp_path)
    assert risky.approval_status == ApprovalStatus.PENDING
