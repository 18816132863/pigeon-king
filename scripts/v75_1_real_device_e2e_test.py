#!/usr/bin/env python3
"""
V75.1 真实设备 E2E 测试套件

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
    """E2E 测试运行器"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0
    
    def log(self, name: str, status: str, message: str = "", data: Any = None):
        """记录测试结果"""
        result = {
            "name": name,
            "status": status,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        if status == "pass":
            self.passed += 1
            print(f"✅ PASS: {name}")
        elif status == "fail":
            self.failed += 1
            print(f"❌ FAIL: {name}")
        else:
            self.skipped += 1
            print(f"⏭️ SKIP: {name}")
        
        if message:
            print(f"       {message}")
    
    def summary(self) -> Dict[str, Any]:
        """生成测试摘要"""
        return {
            "total": len(self.results),
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "results": self.results
        }


async def test_alarm_e2e(runner: E2ETestRunner, call_device_tool=None):
    """测试闹钟 E2E"""
    print("\n[1] 闹钟 E2E 测试")
    
    if call_device_tool is None:
        # 尝试导入真实工具
        try:
            from tools import call_device_tool as real_call
            call_device_tool = real_call
        except ImportError:
            runner.log("alarm_e2e", "skip", "call_device_tool 不可用，需要真实设备连接")
            return
    
    from execution.device_capabilities import AlarmCapability
    
    alarm = AlarmCapability(call_device_tool=call_device_tool)
    
    # 1. 查询闹钟
    alarms, result = await alarm.search(range_type="next")
    if result.is_success():
        runner.log("alarm_search", "pass", f"找到 {len(alarms) if alarms else 0} 个闹钟")
    else:
        runner.log("alarm_search", "fail", result.message)
        return
    
    # 2. 创建闹钟
    test_time = (datetime.now() + timedelta(hours=1)).strftime("%Y%m%d %H%M%S")
    entity_id, result = await alarm.create(
        alarm_time=test_time,
        alarm_title="E2E测试闹钟",
        check_duplicate=True
    )
    if result.is_success() or result.status.value == "skipped":
        runner.log("alarm_create", "pass", f"闹钟已创建或已存在: {entity_id}")
    else:
        runner.log("alarm_create", "fail", result.message)
    
    # 3. 修改闹钟
    if entity_id:
        new_time = (datetime.now() + timedelta(hours=2)).strftime("%Y%m%d %H%M%S")
        result = await alarm.modify(entity_id=entity_id, new_time=new_time)
        if result.is_success():
            runner.log("alarm_modify", "pass", f"闹钟已修改为 {new_time}")
        elif result.status.value == "success_with_timeout_receipt":
            runner.log("alarm_modify", "pass", "超时但二次验证成功")
        else:
            runner.log("alarm_modify", "fail", result.message)
    
    # 4. 删除测试闹钟
    if entity_id:
        result = await alarm.delete_by_title("E2E测试闹钟")
        if result.is_success():
            runner.log("alarm_delete", "pass", "测试闹钟已删除")
        else:
            runner.log("alarm_delete", "fail", result.message)


async def test_hiboard_push_e2e(runner: E2ETestRunner):
    """测试负一屏推送 E2E"""
    print("\n[2] 负一屏推送 E2E 测试")
    
    try:
        from skills.today_task.scripts.task_push import push_task
    except ImportError:
        runner.log("hiboard_push", "skip", "today-task 技能未安装")
        return
    
    # 创建测试推送
    task_data = {
        "task_name": "E2E测试推送",
        "task_content": "# E2E测试\n\n这是一条测试推送，验证负一屏推送功能。",
        "task_result": "测试完成"
    }
    
    try:
        result = await push_task(task_data)
        if result.get("code") == "0000000000":
            runner.log("hiboard_push", "pass", "负一屏推送成功")
        else:
            runner.log("hiboard_push", "fail", str(result))
    except Exception as e:
        runner.log("hiboard_push", "fail", str(e))


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
            runner.log("chat_cron_list", "pass", "cron 列表获取成功")
        else:
            runner.log("chat_cron_list", "fail", result.stderr)
    except FileNotFoundError:
        runner.log("chat_cron_list", "skip", "openclaw 命令不可用")
    except Exception as e:
        runner.log("chat_cron_list", "fail", str(e))


async def test_calendar_e2e(runner: E2ETestRunner, call_device_tool=None):
    """测试日程 E2E"""
    print("\n[4] 日程 E2E 测试")
    
    if call_device_tool is None:
        try:
            from tools import call_device_tool as real_call
            call_device_tool = real_call
        except ImportError:
            runner.log("calendar_e2e", "skip", "call_device_tool 不可用")
            return
    
    from execution.device_capabilities import CalendarCapability
    
    calendar = CalendarCapability(call_device_tool=call_device_tool)
    
    # 查询今天的日程
    today = datetime.now().strftime("%Y%m%d")
    events, result = await calendar.search(
        start_time=f"{today} 000000",
        end_time=f"{today} 235959"
    )
    
    if result.is_success():
        runner.log("calendar_search", "pass", f"找到 {len(events) if events else 0} 个日程")
    elif result.status.value == "skipped":
        runner.log("calendar_search", "skip", "查询结果为空 (-303)")
    else:
        runner.log("calendar_search", "fail", result.message)


async def test_notification_e2e(runner: E2ETestRunner, call_device_tool=None):
    """测试通知 E2E"""
    print("\n[5] 通知 E2E 测试")
    
    runner.log("notification_e2e", "skip", "通知能力暂无对应端侧工具")


async def test_gui_fallback_e2e(runner: E2ETestRunner):
    """测试 GUI fallback E2E"""
    print("\n[6] GUI fallback E2E 测试")
    
    try:
        from xiaoyi_gui_agent import xiaoyi_gui_agent
        runner.log("gui_fallback_available", "pass", "xiaoyi_gui_agent 可用")
    except ImportError:
        runner.log("gui_fallback_available", "skip", "xiaoyi_gui_agent 未安装")


async def test_file_e2e(runner: E2ETestRunner, call_device_tool=None):
    """测试文件动作 E2E"""
    print("\n[7] 文件动作 E2E 测试")
    
    if call_device_tool is None:
        try:
            from tools import call_device_tool as real_call
            call_device_tool = real_call
        except ImportError:
            runner.log("file_e2e", "skip", "call_device_tool 不可用")
            return
    
    from execution.device_capabilities import FileCapability
    
    file_cap = FileCapability(call_device_tool=call_device_tool)
    
    # 搜索文件
    files, result = await file_cap.search("test")
    
    if result.is_success():
        runner.log("file_search", "pass", f"找到 {len(files) if files else 0} 个文件")
    else:
        runner.log("file_search", "fail", result.message)


async def test_device_serial_lane_e2e(runner: E2ETestRunner):
    """测试端侧串行化 E2E"""
    print("\n[8] 端侧串行化 E2E 测试")
    
    try:
        from orchestration.end_side_serial_lanes_v3 import EndSideSerialLaneV3, DeviceAction
        
        lane = EndSideSerialLaneV3()
        
        # 创建多个端侧动作
        actions = [
            DeviceAction("d1", "modify_alarm", "alarm:1", "idemp_1"),
            DeviceAction("d2", "create_calendar", "calendar:1", "idemp_2"),
            DeviceAction("d3", "send_message", "sms:1", "idemp_3"),
        ]
        
        # 模拟执行器
        def mock_executor(action):
            return {"status": "ok", "action_id": action.idempotency_key}
        
        # 串行执行
        receipts = lane.submit_many(actions, mock_executor)
        
        # 验证所有动作都执行了
        if len(receipts) == len(actions):
            runner.log("device_serial_lane", "pass", f"所有 {len(actions)} 个端侧动作串行执行成功")
        else:
            runner.log("device_serial_lane", "fail", f"只执行了 {len(receipts)}/{len(actions)} 个动作")
            
    except ImportError as e:
        runner.log("device_serial_lane", "skip", f"EndSideSerialLaneV3 不可用: {e}")


async def test_interrupt_recovery_e2e(runner: E2ETestRunner):
    """测试中断恢复 E2E"""
    print("\n[9] 中断恢复 E2E 测试")
    
    try:
        from orchestration.state.recovery_store import get_recovery_store, RecoveryAction
        from infrastructure.compact_resume_policy import build_resume_state
        
        # 创建恢复存储
        store = get_recovery_store()
        
        # 模拟中断点
        resume_state = build_resume_state(
            task_id="e2e_test_task",
            version="V75.1",
            phase="interrupt_test",
            pending_steps=["step1", "step2", "step3"]
        )
        
        # 标记 step1 完成
        resume_state.mark_complete("step1")
        
        # 验证恢复状态
        if "step1" in resume_state.completed_steps and "step2" in resume_state.pending_steps:
            runner.log("interrupt_recovery", "pass", "中断恢复状态正确：completed_steps 和 pending_steps 分离")
        else:
            runner.log("interrupt_recovery", "fail", f"恢复状态异常: completed={resume_state.completed_steps}, pending={resume_state.pending_steps}")
            
    except ImportError as e:
        runner.log("interrupt_recovery", "skip", f"恢复模块不可用: {e}")


async def test_capability_extension_e2e(runner: E2ETestRunner):
    """测试能力扩展闭环 E2E"""
    print("\n[10] 能力扩展闭环 E2E 测试")
    
    try:
        from agent_kernel.capability_extension import CapabilityExtension
        from infrastructure.skill_supply_chain_attestation_v7 import SkillSupplyChainAttestationV7
        
        ext = CapabilityExtension()
        
        # 模拟能力缺口
        gap = {
            "name": "test_capability",
            "description": "测试能力",
            "required": True
        }
        
        # 评估扩展
        evaluation = ext.evaluate(gap)
        
        if evaluation.confidence >= 0.6:
            runner.log("capability_extension", "pass", f"能力扩展评估通过: confidence={evaluation.confidence}")
        else:
            runner.log("capability_extension", "fail", f"能力扩展评估失败: {evaluation.reasons}")
            
    except ImportError as e:
        runner.log("capability_extension", "skip", f"能力扩展模块不可用: {e}")


async def main():
    """运行所有 E2E 测试"""
    print("=" * 60)
    print("V75.1 真实设备 E2E 测试套件")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    runner = E2ETestRunner()
    
    # 运行所有测试
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
    
    # 生成报告
    summary = runner.summary()
    
    print("\n" + "=" * 60)
    print("E2E 测试摘要")
    print("=" * 60)
    print(f"总计: {summary['total']}")
    print(f"通过: {summary['passed']}")
    print(f"失败: {summary['failed']}")
    print(f"跳过: {summary['skipped']}")
    
    # 保存报告
    report_path = "V75_1_REAL_DEVICE_E2E_REPORT.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {report_path}")
    
    return 0 if summary['failed'] == 0 else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
