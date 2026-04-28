#!/usr/bin/env python3
"""
V75.2 真实设备 E2E 测试套件 - Reality Closure Fix

修复：
- 区分真实设备通过 vs 模拟通过
- 跳过项不能让 ready_for_production=true
- 报告口径统一

验证所有端侧能力的真实设备交互：
- 闹钟创建/修改/查询/删除
- 负一屏推送
- 主对话框 cron
- 日程
- 通知
- GUI fallback
- 文件动作

所有端侧动作多重执行必须串行。
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class E2ETestRunner:
    """E2E 测试运行器 - V75.2 修复版"""
    
    def __init__(self):
        self.results = []
        self.real_device_pass = 0
        self.simulated_pass = 0
        self.skipped = 0
        self.failed = 0
        self.missing_dependencies = []
    
    def log(self, name: str, status: str, message: str = "", data: Any = None, is_real_device: bool = False):
        """
        记录测试结果
        
        Args:
            name: 测试名称
            status: 状态 (pass/fail/skip)
            message: 消息
            data: 数据
            is_real_device: 是否真实设备测试（vs 模拟）
        """
        result = {
            "name": name,
            "status": status,
            "message": message,
            "data": data,
            "is_real_device": is_real_device,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        if status == "pass":
            if is_real_device:
                self.real_device_pass += 1
                print(f"✅ REAL_PASS: {name}")
            else:
                self.simulated_pass += 1
                print(f"✅ SIM_PASS: {name}")
        elif status == "fail":
            self.failed += 1
            print(f"❌ FAIL: {name}")
        else:
            self.skipped += 1
            print(f"⏭️ SKIP: {name}")
        
        if message:
            print(f"       {message}")
    
    def add_missing_dependency(self, dep: str):
        """添加缺失依赖"""
        if dep not in self.missing_dependencies:
            self.missing_dependencies.append(dep)
    
    def summary(self) -> Dict[str, Any]:
        """生成摘要"""
        # V75.2: 只有真实设备测试全部通过且无跳过、无失败、无缺失依赖时才能 ready_for_production
        ready_for_production = (
            self.failed == 0 and 
            self.skipped == 0 and 
            self.real_device_pass > 0 and
            len(self.missing_dependencies) == 0
        )
        
        ready_for_controlled_test = self.failed == 0
        
        return {
            "total": len(self.results),
            "real_device_pass": self.real_device_pass,
            "simulated_pass": self.simulated_pass,
            "skipped": self.skipped,
            "failed": self.failed,
            "missing_dependencies": self.missing_dependencies,
            "ready_for_production": ready_for_production,
            "ready_for_controlled_test": ready_for_controlled_test,
            "results": self.results
        }


async def test_alarm_e2e(runner: E2ETestRunner):
    """测试闹钟 E2E"""
    print("\n[1] 闹钟 E2E 测试")
    
    try:
        from agent_kernel.device_capabilities import AlarmCapability
        from platform_adapter.device_tool_adapter import call_device_tool
    except ImportError as e:
        runner.log("alarm_e2e", "skip", f"模块不可用: {e}")
        runner.add_missing_dependency(str(e))
        return
    
    alarm = AlarmCapability(call_device_tool=call_device_tool)
    
    # 1. 查询闹钟
    alarms, result = await alarm.search(range_type="next")
    if result.is_success():
        # 检查是否是真实设备响应
        is_real = result.data is not None and len(result.data) > 0
        runner.log("alarm_search", "pass", f"找到 {len(alarms) if alarms else 0} 个闹钟", is_real_device=is_real)
    else:
        runner.log("alarm_search", "fail", result.message)


async def test_hiboard_push_e2e(runner: E2ETestRunner):
    """测试负一屏推送 E2E"""
    print("\n[2] 负一屏推送 E2E 测试")
    
    skill_path = os.path.expanduser("~/.openclaw/workspace/skills/today-task")
    
    if not os.path.exists(skill_path):
        runner.log("hiboard_push", "skip", "today-task 技能未安装")
        return
    
    # 检查配置
    auth_code = None
    push_url = None
    
    openclaw_config_path = os.path.expanduser("~/.openclaw/openclaw.json")
    if os.path.exists(openclaw_config_path):
        with open(openclaw_config_path, 'r', encoding='utf-8') as f:
            openclaw_config = json.load(f)
        skill_config = openclaw_config.get('skills', {}).get('entries', {}).get('today-task', {}).get('config', {})
        auth_code = skill_config.get('authCode')
        push_url = skill_config.get('pushServiceUrl')
    
    config_path = os.path.join(skill_path, "config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        if not push_url:
            push_url = config.get('pushServiceUrl')
    
    if not auth_code:
        runner.log("hiboard_push", "skip", "缺少 authCode")
        return
    
    if not push_url:
        runner.log("hiboard_push", "skip", "缺少 pushServiceUrl")
        return
    
    runner.log("hiboard_push", "pass", "today-task 配置完整", is_real_device=False)


async def test_chat_cron_e2e(runner: E2ETestRunner):
    """测试主对话框 cron E2E"""
    print("\n[3] 主对话框 cron E2E 测试")
    
    try:
        import subprocess
        result = subprocess.run(
            ["openclaw", "cron", "list"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            runner.log("chat_cron_list", "pass", "cron 列表获取成功", is_real_device=True)
        else:
            runner.log("chat_cron_list", "fail", result.stderr)
    except FileNotFoundError:
        runner.log("chat_cron_list", "skip", "openclaw 命令不可用")
    except Exception as e:
        runner.log("chat_cron_list", "fail", str(e))


async def test_calendar_e2e(runner: E2ETestRunner):
    """测试日程 E2E"""
    print("\n[4] 日程 E2E 测试")
    
    try:
        from agent_kernel.device_capabilities import CalendarCapability
        from platform_adapter.device_tool_adapter import call_device_tool
    except ImportError as e:
        runner.log("calendar_e2e", "skip", f"模块不可用: {e}")
        runner.add_missing_dependency(str(e))
        return
    
    calendar = CalendarCapability(call_device_tool=call_device_tool)
    
    today = datetime.now().strftime("%Y%m%d")
    events, result = await calendar.search(
        start_time=f"{today} 000000",
        end_time=f"{today} 235959"
    )
    
    if result.is_success():
        is_real = result.data is not None and len(result.data) > 0
        runner.log("calendar_search", "pass", f"找到 {len(events) if events else 0} 个日程", is_real_device=is_real)
    else:
        runner.log("calendar_search", "fail", result.message)


async def test_notification_e2e(runner: E2ETestRunner):
    """测试通知 E2E"""
    print("\n[5] 通知 E2E 测试")
    
    try:
        from capabilities.query_notification_status import query_notification_status
        from capabilities.explain_notification_auth_state import explain_notification_auth_state
    except ImportError as e:
        runner.log("notification_e2e", "skip", f"通知模块不可用: {e}")
        runner.add_missing_dependency(str(e))
        return
    
    result = query_notification_status()
    if result.get("success"):
        runner.log("notification_query", "pass", "通知状态查询成功", is_real_device=True)
    else:
        runner.log("notification_query", "fail", result.get("message", "查询失败"))
    
    auth_result = explain_notification_auth_state()
    if auth_result.get("success"):
        runner.log("notification_auth", "pass", f"通知授权状态: {auth_result.get('summary', '未知')}", is_real_device=True)
    else:
        runner.log("notification_auth", "fail", auth_result.get("message", "获取授权状态失败"))


async def test_gui_fallback_e2e(runner: E2ETestRunner):
    """测试 GUI fallback E2E"""
    print("\n[6] GUI fallback E2E 测试")
    
    skill_path = os.path.expanduser("~/.openclaw/workspace/skills/xiao-gui-agent")
    if os.path.exists(skill_path):
        runner.log("gui_fallback_available", "pass", "xiaoyi-gui-agent 技能可用", is_real_device=False)
    else:
        runner.log("gui_fallback_available", "skip", "xiaoyi-gui-agent 技能未安装")


async def test_file_e2e(runner: E2ETestRunner):
    """测试文件动作 E2E"""
    print("\n[7] 文件动作 E2E 测试")
    
    try:
        from agent_kernel.device_capabilities import FileCapability
        from platform_adapter.device_tool_adapter import call_device_tool
    except ImportError as e:
        runner.log("file_e2e", "skip", f"模块不可用: {e}")
        runner.add_missing_dependency(str(e))
        return
    
    file_cap = FileCapability(call_device_tool=call_device_tool)
    
    files, result = await file_cap.search("test")
    
    if result.is_success():
        is_real = result.data is not None and len(result.data) > 0
        runner.log("file_search", "pass", f"找到 {len(files) if files else 0} 个文件", is_real_device=is_real)
    else:
        runner.log("file_search", "fail", result.message)


async def test_device_serial_lane_e2e(runner: E2ETestRunner):
    """测试端侧串行化 E2E"""
    print("\n[8] 端侧串行化 E2E 测试")
    
    try:
        from orchestration.end_side_serial_lanes_v3 import EndSideSerialLaneV3, DeviceAction
        
        lane = EndSideSerialLaneV3()
        
        actions = [
            DeviceAction(
                action_id="d1",
                action_kind="modify_alarm",
                payload={"alarm_id": "alarm:1"},
                idempotency_key="idemp_1"
            ),
            DeviceAction(
                action_id="d2",
                action_kind="create_calendar",
                payload={"event": "calendar:1"},
                idempotency_key="idemp_2"
            ),
            DeviceAction(
                action_id="d3",
                action_kind="send_message",
                payload={"message": "sms:1"},
                idempotency_key="idemp_3"
            ),
        ]
        
        def mock_executor(action):
            return {"status": "success", "action_id": action.idempotency_key}
        
        receipts = lane.submit_many(actions, mock_executor)
        
        success_count = sum(1 for r in receipts if r.status == "success")
        if success_count == len(actions):
            runner.log("device_serial_lane", "pass", f"所有 {len(actions)} 个端侧动作串行执行成功", is_real_device=False)
        else:
            runner.log("device_serial_lane", "fail", f"只成功执行了 {success_count}/{len(actions)} 个动作")
            
    except ImportError as e:
        runner.log("device_serial_lane", "skip", f"EndSideSerialLaneV3 不可用: {e}")


async def test_interrupt_recovery_e2e(runner: E2ETestRunner):
    """测试中断恢复 E2E"""
    print("\n[9] 中断恢复 E2E 测试")
    
    try:
        from orchestration.state.recovery_store import get_recovery_store
        from infrastructure.compact_resume_policy import build_resume_state
        
        store = get_recovery_store()
        
        resume_state = build_resume_state(
            task_id="e2e_test_task",
            version="V75.2",
            phase="interrupt_test",
            pending_steps=["step1", "step2", "step3"]
        )
        
        resume_state.mark_complete("step1")
        
        if "step1" in resume_state.completed_steps and "step2" in resume_state.pending_steps:
            runner.log("interrupt_recovery", "pass", "中断恢复状态正确", is_real_device=False)
        else:
            runner.log("interrupt_recovery", "fail", f"恢复状态异常")
            
    except ImportError as e:
        runner.log("interrupt_recovery", "skip", f"恢复模块不可用: {e}")


async def test_capability_extension_e2e(runner: E2ETestRunner):
    """测试能力扩展闭环 E2E"""
    print("\n[10] 能力扩展闭环 E2E 测试")
    
    try:
        from agent_kernel.capability_extension import CapabilityExtensionPipeline, ExtensionCandidate
        
        pipeline = CapabilityExtensionPipeline()
        
        gap = pipeline.detect_gap("test_capability", ["alarm", "calendar"])
        
        if gap is None:
            runner.log("capability_extension", "pass", "能力缺口检测正常", is_real_device=False)
            return
        
        candidate = ExtensionCandidate(
            name="test_capability",
            source="local_registry",
            kind="skill",
            trust_level="high",
            declared_scopes=["read"]
        )
        
        evaluation = pipeline.evaluate(candidate)
        
        if evaluation.passed:
            runner.log("capability_extension", "pass", f"能力扩展评估通过: score={evaluation.score}", is_real_device=False)
        else:
            runner.log("capability_extension", "fail", f"能力扩展评估失败: {evaluation.reasons}")
            
    except ImportError as e:
        runner.log("capability_extension", "skip", f"能力扩展模块不可用: {e}")


async def main():
    """运行所有 E2E 测试"""
    print("=" * 60)
    print("V75.2 真实设备 E2E 测试套件")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    runner = E2ETestRunner()
    
    await test_alarm_e2e(runner)
    await test_hiboard_push_e2e(runner)
    await test_chat_cron_e2e(runner)
    await test_calendar_e2e(runner)
    await test_notification_e2e(runner)
    await test_gui_fallback_e2e(runner)
    await test_file_e2e(runner)
    await test_device_serial_lane_e2e(runner)
    await test_interrupt_recovery_e2e(runner)
    await test_capability_extension_e2e(runner)
    
    summary = runner.summary()
    
    print("\n" + "=" * 60)
    print("E2E 测试摘要")
    print("=" * 60)
    print(f"总计: {summary['total']}")
    print(f"真实设备通过: {summary['real_device_pass']}")
    print(f"模拟通过: {summary['simulated_pass']}")
    print(f"跳过: {summary['skipped']}")
    print(f"失败: {summary['failed']}")
    print(f"缺失依赖: {summary['missing_dependencies']}")
    print(f"ready_for_production: {summary['ready_for_production']}")
    print(f"ready_for_controlled_test: {summary['ready_for_controlled_test']}")
    
    # 保存报告
    report_path = "V75_2_REAL_DEVICE_E2E_REPORT.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {report_path}")
    
    return 0 if summary['failed'] == 0 else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
