from pathlib import Path


def test_v147_action_dsl():
    from core.action_bridge import ActionDSLCompiler
    a = ActionDSLCompiler().compile("给客户发送邮件")
    assert a.kind.value == "send"
    assert a.requires_approval


def test_v148_device_session(tmp_path: Path):
    from core.action_bridge import DeviceSessionManager
    d = DeviceSessionManager(tmp_path).best_for("dry_run")
    assert d.status.value == "connected"


def test_v149_adapter_registry(tmp_path: Path):
    from core.action_bridge import ToolAdapterRegistry
    from core.action_bridge.schemas import ActionKind
    a = ToolAdapterRegistry(tmp_path).select(ActionKind.WRITE)
    assert a.status.value == "active"


def test_v150_evidence_capture(tmp_path: Path):
    from core.action_bridge import EvidenceCapture
    from core.action_bridge.schemas import EvidenceKind
    e = EvidenceCapture(tmp_path)
    e.record("r1", EvidenceKind.INPUT, "input", {"x": 1})
    assert len(e.list_run("r1")) == 1


def test_v151_side_effect_executor(tmp_path: Path):
    from core.action_bridge import ActionDSLCompiler, ToolAdapterRegistry, SideEffectExecutor
    a = ActionDSLCompiler().compile("给客户发送邮件")
    adapter = ToolAdapterRegistry(tmp_path).select(a.kind)
    r = SideEffectExecutor().execute(a, adapter, approved=False)
    assert r.status.value == "waiting_approval"


def test_v152_notification_center(tmp_path: Path):
    from core.action_bridge import NotificationCenter
    from core.action_bridge.schemas import NotificationLevel
    n = NotificationCenter(tmp_path)
    n.notify(NotificationLevel.INFO, "t", "m")
    assert n.list_all()


def test_v153_handoff_inbox(tmp_path: Path):
    from core.action_bridge import HandoffInbox
    h = HandoffInbox(tmp_path)
    item = h.create("approve", "reason", "a1")
    assert h.open_items()
    assert h.resolve(item.id, True).status.value == "resolved"


def test_v154_background_run_ledger(tmp_path: Path):
    from core.action_bridge import BackgroundRunLedger
    from core.action_bridge.schemas import BackgroundRunStatus
    b = BackgroundRunLedger(tmp_path)
    r = b.create("run", {"id": "c"}, waiting=True)
    assert r.status == BackgroundRunStatus.WAITING


def test_v155_real_world_scenario_harness():
    from core.action_bridge import RealWorldScenarioHarness
    r = RealWorldScenarioHarness().evaluate({
        "action_compiled": True,
        "adapter_selected": True,
        "evidence_recorded": True,
        "notification_created": True,
        "high_risk": True,
        "handoff_created": True,
        "no_unapproved_side_effect": True,
        "background_checkpoint": True,
    })
    assert r.passed


def test_v156_action_bridge_kernel(tmp_path: Path):
    from core.action_bridge import run_action_bridge_cycle
    from core.action_bridge.schemas import BridgeStatus
    r = run_action_bridge_cycle("安装未知插件并执行", root=tmp_path)
    assert r.bridge_status == BridgeStatus.WAITING_APPROVAL
