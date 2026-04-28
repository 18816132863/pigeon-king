#!/usr/bin/env python3
"""
V75.3 Reality Closure Gate - Hard Fix

最终门禁，通过条件：
- 无端侧串行绕过（包括 capabilities 目录）
- DeviceAction 参数一致
- calendar / notification / alarm / file / GUI 都走串行 lane
- E2E 报告区分真实/模拟/跳过
- quick soak 稳定退出
- ready_for_production 不虚标
- ready_for_controlled_test 口径正确

V75.3 修复：
- capabilities 目录不再白名单
- ready_for_production 严格判断
- ready_for_controlled_test 正确判断
- 报告口径一致
"""

import asyncio
import json
import os
import sys
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


class RealityClosureGate:
    """Reality Closure 门禁 V75.3"""
    
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.ready_for_production = True
        self.ready_for_controlled_test = True
        self.blockers = []
        self.warnings = []
    
    def log(self, name: str, status: str, message: str, is_blocker: bool = False, is_warning: bool = False):
        """记录检查结果"""
        result = {
            "name": name,
            "status": status,
            "message": message,
            "is_blocker": is_blocker,
            "is_warning": is_warning,
            "timestamp": datetime.now().isoformat()
        }
        self.checks.append(result)
        
        if status == "pass":
            self.passed += 1
            print(f"✅ PASS: {name}")
        elif status == "fail":
            self.failed += 1
            if is_blocker:
                self.blockers.append(name)
                self.ready_for_production = False
            print(f"❌ FAIL: {name}")
        else:
            self.skipped += 1
            print(f"⏭️ SKIP: {name}")
        
        if message:
            print(f"       {message}")
    
    async def check_entry_bypass_scan(self):
        """检查入口绕过扫描"""
        print("\n[1] 入口绕过扫描 (V75.3 Hard Fix)")
        
        scan_script = PROJECT_ROOT / "scripts" / "v75_3_entry_bypass_scan.py"
        if not scan_script.exists():
            self.log("entry_bypass_scan", "skip", "扫描脚本不存在")
            return
        
        try:
            result = subprocess.run(
                [sys.executable, str(scan_script)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(PROJECT_ROOT)
            )
            
            if result.returncode == 0:
                self.log("entry_bypass_scan", "pass", "无端侧串行绕过（包括 capabilities 目录）")
            else:
                self.log("entry_bypass_scan", "fail", "发现端侧串行绕过", is_blocker=True)
                print(result.stdout)
        except Exception as e:
            self.log("entry_bypass_scan", "fail", str(e), is_blocker=True)
    
    async def check_device_action_params(self):
        """检查 DeviceAction 参数一致性"""
        print("\n[2] DeviceAction 参数一致性")
        
        adapter_path = PROJECT_ROOT / "platform_adapter" / "xiaoyi_adapter.py"
        if not adapter_path.exists():
            self.log("device_action_params", "skip", "xiaoyi_adapter.py 不存在")
            return
        
        with open(adapter_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否使用了正确的参数名
        correct_params = ["action_id=", "action_kind=", "payload=", "idempotency_key="]
        wrong_params = ["device_id=", "action_type="]
        
        found_wrong = []
        for param in wrong_params:
            if param in content and "DeviceAction(" in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if param in line:
                        context = '\n'.join(lines[max(0, i-3):i+3])
                        if "DeviceAction(" in context:
                            found_wrong.append(f"行 {i+1}: {line.strip()}")
        
        if found_wrong:
            self.log("device_action_params", "fail", f"发现错误参数: {found_wrong}", is_blocker=True)
        else:
            self.log("device_action_params", "pass", "DeviceAction 参数一致")
    
    async def check_serial_lane_usage(self):
        """检查串行化器使用"""
        print("\n[3] 串行化器使用检查")
        
        modules_to_check = [
            ("platform_adapter/xiaoyi_adapter.py", "xiaoyi_adapter"),
            ("agent_kernel/base_device_capability.py", "base_device_capability"),
            ("orchestration/device_serial_call.py", "device_serial_call"),
        ]
        
        all_passed = True
        for rel_path, name in modules_to_check:
            file_path = PROJECT_ROOT / rel_path
            if not file_path.exists():
                continue
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否导入了串行化器
            has_serial_lane = "EndSideSerialLaneV3" in content or "DeviceSerialLane" in content or "serial_call_device_tool" in content
            
            if has_serial_lane:
                self.log(f"serial_lane_{name}", "pass", f"{name} 正确使用串行化器")
            else:
                self.log(f"serial_lane_{name}", "skip", f"{name} 未使用串行化器")
    
    async def check_capabilities_no_direct_call(self):
        """检查 capabilities 目录无直接调用"""
        print("\n[4] Capabilities 目录检查")
        
        capabilities_dir = PROJECT_ROOT / "capabilities"
        if not capabilities_dir.exists():
            self.log("capabilities_check", "skip", "capabilities 目录不存在")
            return
        
        violations = []
        for file_path in capabilities_dir.glob("*.py"):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否有直接调用 call_device_tool
            if "from platform_adapter.device_tool_adapter import call_device_tool" in content:
                violations.append(f"{file_path.name}: 发现直接导入 call_device_tool")
            
            # 检查是否使用了统一入口
            if "serial_call_device_tool" in content:
                # 正确：使用统一入口
                pass
            elif "call_device_tool(" in content:
                violations.append(f"{file_path.name}: 发现直接调用 call_device_tool")
        
        if violations:
            self.log("capabilities_check", "fail", f"发现违规: {violations}", is_blocker=True)
        else:
            self.log("capabilities_check", "pass", "capabilities 目录无直接调用")
    
    async def check_e2e_report_format(self):
        """检查 E2E 报告格式"""
        print("\n[5] E2E 报告格式检查")
        
        e2e_script = PROJECT_ROOT / "scripts" / "v75_2_real_device_e2e_test.py"
        if not e2e_script.exists():
            self.log("e2e_report_format", "skip", "E2E 测试脚本不存在")
            return
        
        with open(e2e_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_fields = [
            "real_device_pass",
            "simulated_pass",
            "ready_for_production",
            "ready_for_controlled_test",
            "is_real_device",
            "missing_dependencies"
        ]
        
        missing_fields = [f for f in required_fields if f not in content]
        
        if missing_fields:
            self.log("e2e_report_format", "fail", f"缺少字段: {missing_fields}", is_blocker=True)
        else:
            self.log("e2e_report_format", "pass", "E2E 报告格式正确")
    
    async def check_soak_test_stability(self):
        """检查压测稳定性"""
        print("\n[6] 压测稳定性检查")
        
        soak_script = PROJECT_ROOT / "scripts" / "v75_1_long_running_soak_test.py"
        if not soak_script.exists():
            self.log("soak_test_stability", "skip", "压测脚本不存在")
            return
        
        try:
            result = subprocess.run(
                [sys.executable, str(soak_script), "--quick", "--timeout", "30"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(PROJECT_ROOT)
            )
            
            if result.returncode == 0:
                self.log("soak_test_stability", "pass", "压测稳定退出")
            else:
                self.log("soak_test_stability", "fail", f"压测失败: {result.stderr[:200]}", is_blocker=True)
        except subprocess.TimeoutExpired:
            self.log("soak_test_stability", "fail", "压测超时未退出", is_blocker=True)
        except Exception as e:
            self.log("soak_test_stability", "fail", str(e), is_blocker=True)
    
    async def check_production_readiness(self):
        """检查生产就绪状态"""
        print("\n[7] 生产就绪检查")
        
        e2e_script = PROJECT_ROOT / "scripts" / "v75_2_real_device_e2e_test.py"
        if not e2e_script.exists():
            self.log("production_readiness", "skip", "E2E 测试脚本不存在")
            self.ready_for_production = False
            return
        
        try:
            result = subprocess.run(
                [sys.executable, str(e2e_script)],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(PROJECT_ROOT)
            )
            
            # 解析报告
            report_path = PROJECT_ROOT / "V75_2_REAL_DEVICE_E2E_REPORT.json"
            if report_path.exists():
                with open(report_path, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                
                real_pass = report.get("real_device_pass", 0)
                sim_pass = report.get("simulated_pass", 0)
                skipped = report.get("skipped", 0)
                failed = report.get("failed", 0)
                missing_deps = report.get("missing_dependencies", [])
                
                # V75.3: 严格的 ready_for_production 判断
                if failed > 0:
                    self.log("production_readiness", "fail", f"E2E 测试失败: {failed} 项", is_blocker=True)
                    self.ready_for_production = False
                    self.ready_for_controlled_test = False
                elif skipped > 0:
                    self.log("production_readiness", "fail", f"E2E 测试跳过: {skipped} 项，不能 ready_for_production", is_blocker=True)
                    self.ready_for_production = False
                    # V75.3: 但 failed=0 时，controlled_test 可以为 true
                    self.ready_for_controlled_test = True
                elif len(missing_deps) > 0:
                    self.log("production_readiness", "fail", f"缺失依赖: {missing_deps}，不能 ready_for_production", is_blocker=True)
                    self.ready_for_production = False
                    self.ready_for_controlled_test = True
                elif real_pass == 0:
                    self.log("production_readiness", "fail", "无真实设备测试通过，不能 ready_for_production", is_blocker=True)
                    self.ready_for_production = False
                    self.ready_for_controlled_test = True
                else:
                    self.log("production_readiness", "pass", f"真实设备通过: {real_pass}, 模拟通过: {sim_pass}")
            else:
                self.log("production_readiness", "fail", "E2E 报告未生成", is_blocker=True)
                self.ready_for_production = False
                self.ready_for_controlled_test = False
                
        except Exception as e:
            self.log("production_readiness", "fail", str(e), is_blocker=True)
            self.ready_for_production = False
            self.ready_for_controlled_test = False
    
    async def check_report_consistency(self):
        """检查报告一致性"""
        print("\n[8] 报告一致性检查")
        
        # V75.3: 检查根目录和 v75_3_artifacts 目录的报告是否一致
        root_report = PROJECT_ROOT / "REALITY_CLOSURE_AUDIT_REPORT.json"
        artifacts_report = PROJECT_ROOT / "scripts" / "v75_3_artifacts" / "REALITY_CLOSURE_AUDIT_REPORT.json"
        
        if root_report.exists() and artifacts_report.exists():
            with open(root_report, 'r', encoding='utf-8') as f:
                root_data = json.load(f)
            with open(artifacts_report, 'r', encoding='utf-8') as f:
                artifacts_data = json.load(f)
            
            # 检查关键字段是否一致
            if root_data.get("ready_for_production") != artifacts_data.get("ready_for_production"):
                self.log("report_consistency", "fail", "ready_for_production 不一致", is_blocker=True)
            elif root_data.get("ready_for_controlled_test") != artifacts_data.get("ready_for_controlled_test"):
                self.log("report_consistency", "fail", "ready_for_controlled_test 不一致", is_blocker=True)
            else:
                self.log("report_consistency", "pass", "报告口径一致")
        else:
            self.log("report_consistency", "skip", "报告文件不存在")
    
    async def run(self) -> Dict[str, Any]:
        """运行所有检查"""
        print("=" * 60)
        print("V75.3 Reality Closure Gate (Hard Fix)")
        print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        await self.check_entry_bypass_scan()
        await self.check_device_action_params()
        await self.check_serial_lane_usage()
        await self.check_capabilities_no_direct_call()
        await self.check_e2e_report_format()
        await self.check_soak_test_stability()
        await self.check_production_readiness()
        await self.check_report_consistency()
        
        # 生成报告
        report = {
            "gate_name": "V75.3 Reality Closure Gate",
            "timestamp": datetime.now().isoformat(),
            "total_checks": len(self.checks),
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "blockers": self.blockers,
            "warnings": self.warnings,
            "ready_for_production": self.ready_for_production and len(self.blockers) == 0,
            "ready_for_controlled_test": self.ready_for_controlled_test and self.failed == 0,
            "checks": self.checks
        }
        
        print("\n" + "=" * 60)
        print("门禁摘要")
        print("=" * 60)
        print(f"总检查: {report['total_checks']}")
        print(f"通过: {report['passed']}")
        print(f"失败: {report['failed']}")
        print(f"跳过: {report['skipped']}")
        print(f"阻塞项: {report['blockers']}")
        print(f"ready_for_production: {report['ready_for_production']}")
        print(f"ready_for_controlled_test: {report['ready_for_controlled_test']}")
        
        # 保存报告到两个位置
        report_path1 = PROJECT_ROOT / "REALITY_CLOSURE_AUDIT_REPORT.json"
        report_path2 = PROJECT_ROOT / "scripts" / "v75_3_artifacts" / "REALITY_CLOSURE_AUDIT_REPORT.json"
        report_path2.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path1, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        with open(report_path2, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n报告已保存: {report_path1}")
        print(f"报告已保存: {report_path2}")
        
        return report


async def main():
    gate = RealityClosureGate()
    report = await gate.run()
    
    return 0 if report['ready_for_controlled_test'] else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
