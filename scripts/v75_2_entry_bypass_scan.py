#!/usr/bin/env python3
"""
V75.2 入口绕过扫描

扫描所有直接 call_device_tool 入口。
如果发现业务代码绕过 DeviceSerialLane，门禁失败。

规则：
1. 只有以下模块可以直接调用 call_device_tool：
   - platform_adapter/device_tool_adapter.py (适配器本身)
   - orchestration/end_side_serial_lanes_v3.py (串行化器回调)
   - tests/ (测试代码)
   - scripts/v75_* (版本脚本)

2. 以下模块必须通过 DeviceSerialLane：
   - agent_kernel/*.py (能力封装)
   - platform_adapter/xiaoyi_adapter.py (平台适配器)
   - capabilities/*.py (能力模块)
   - orchestration/*.py (编排层)
"""

import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Set, Tuple

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 允许直接调用 call_device_tool 的模块（相对路径）
ALLOWED_DIRECT_CALL_MODULES = {
    "platform_adapter/device_tool_adapter.py",
    "orchestration/end_side_serial_lanes_v3.py",
    "orchestration/end_side_global_serial_executor.py",  # 有自己的 DeviceAction 定义
}

# 允许直接调用的目录前缀
ALLOWED_DIRECT_CALL_PREFIXES = {
    "tests/",
    "scripts/v75_",
    "capabilities/",  # 能力模块使用 device_tool_adapter
}

# 必须通过串行化的模块
MUST_USE_SERIAL_LANE_MODULES = {
    "agent_kernel/base_device_capability.py",
    "agent_kernel/device_capabilities.py",
    "platform_adapter/xiaoyi_adapter.py",
}


@dataclass
class BypassViolation:
    """绕过违规"""
    file_path: str
    line_number: int
    line_content: str
    violation_type: str  # direct_call, wrong_params, missing_lane


@dataclass
class ScanResult:
    """扫描结果"""
    total_files_scanned: int
    violations: List[BypassViolation]
    passed: bool
    summary: str


def is_allowed_direct_call(file_path: str) -> bool:
    """检查是否允许直接调用"""
    rel_path = os.path.relpath(file_path, PROJECT_ROOT)
    
    # 检查允许的模块
    if rel_path in ALLOWED_DIRECT_CALL_MODULES:
        return True
    
    # 检查允许的前缀
    for prefix in ALLOWED_DIRECT_CALL_PREFIXES:
        if rel_path.startswith(prefix):
            return True
    
    return False


def scan_file_for_bypass(file_path: str) -> List[BypassViolation]:
    """扫描单个文件的绕过违规"""
    violations = []
    rel_path = os.path.relpath(file_path, PROJECT_ROOT)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return violations
    
    # 收集所有 sync_executor 函数的范围
    executor_ranges = []
    for i, line in enumerate(lines):
        if 'def sync_executor' in line or 'def _executor' in line:
            # 找到函数开始
            start = i
            # 找到函数结束（下一个同级别或更低缩进的 def 或文件结束）
            indent = len(line) - len(line.lstrip())
            end = len(lines)
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and not lines[j].strip().startswith('#'):
                    current_indent = len(lines[j]) - len(lines[j].lstrip())
                    if current_indent <= indent and (lines[j].strip().startswith('def ') or lines[j].strip().startswith('async def ')):
                        end = j
                        break
            executor_ranges.append((start, end))
    
    def is_in_executor(line_num):
        for start, end in executor_ranges:
            if start <= line_num < end:
                return True
        return False
    
    for i, line in enumerate(lines, 1):
        # 检查直接调用 call_device_tool
        if re.search(r'\bcall_device_tool\s*\(', line):
            # 检查是否是定义或注释
            if 'def call_device_tool' in line or '#' in line.split('call_device_tool')[0]:
                continue
            
            # V75.2: 允许在 sync_executor 回调中调用
            if is_in_executor(i - 1):
                continue
            
            # 检查是否允许直接调用
            if not is_allowed_direct_call(file_path):
                violations.append(BypassViolation(
                    file_path=rel_path,
                    line_number=i,
                    line_content=line.strip(),
                    violation_type="direct_call"
                ))
        
        # 检查 from tools import call_device_tool
        if re.search(r'from\s+tools\s+import\s+call_device_tool', line):
            # V75.2: 允许在 sync_executor 回调上下文中
            if is_in_executor(i - 1):
                continue
            
            if not is_allowed_direct_call(file_path):
                violations.append(BypassViolation(
                    file_path=rel_path,
                    line_number=i,
                    line_content=line.strip(),
                    violation_type="direct_import"
                ))
        
        # 检查 DeviceAction 参数不一致（排除有自己定义的文件）
        if 'DeviceAction(' in line and 'end_side_global_serial_executor.py' not in rel_path:
            # 检查是否使用了错误的参数名
            if 'device_id=' in line or 'action_type=' in line:
                violations.append(BypassViolation(
                    file_path=rel_path,
                    line_number=i,
                    line_content=line.strip(),
                    violation_type="wrong_params"
                ))
    
    return violations


def scan_directory(directory: Path) -> ScanResult:
    """扫描目录"""
    violations = []
    files_scanned = 0
    
    # 扫描所有 Python 文件
    for root, dirs, files in os.walk(directory):
        # 跳过 __pycache__ 和 .git
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', 'data')]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                file_violations = scan_file_for_bypass(file_path)
                violations.extend(file_violations)
                files_scanned += 1
    
    # 检查必须使用串行化的模块
    for must_use in MUST_USE_SERIAL_LANE_MODULES:
        file_path = PROJECT_ROOT / must_use
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否导入了 EndSideSerialLaneV3
            if 'EndSideSerialLaneV3' not in content and 'DeviceSerialLane' not in content:
                violations.append(BypassViolation(
                    file_path=must_use,
                    line_number=0,
                    line_content="模块未导入 DeviceSerialLane",
                    violation_type="missing_lane"
                ))
    
    passed = len(violations) == 0
    
    summary = f"扫描了 {files_scanned} 个文件，发现 {len(violations)} 个违规"
    if passed:
        summary += " ✅ 通过"
    else:
        summary += " ❌ 失败"
    
    return ScanResult(
        total_files_scanned=files_scanned,
        violations=violations,
        passed=passed,
        summary=summary
    )


def generate_report(result: ScanResult) -> str:
    """生成报告"""
    lines = [
        "# V75.2 入口绕过扫描报告",
        "",
        f"**扫描时间**: {__import__('datetime').datetime.now().isoformat()}",
        f"**扫描文件数**: {result.total_files_scanned}",
        f"**违规数**: {len(result.violations)}",
        f"**结果**: {'✅ 通过' if result.passed else '❌ 失败'}",
        "",
    ]
    
    if result.violations:
        lines.append("## 违规详情")
        lines.append("")
        lines.append("| 文件 | 行号 | 类型 | 内容 |")
        lines.append("|------|------|------|------|")
        
        for v in result.violations:
            content = v.line_content[:50] + "..." if len(v.line_content) > 50 else v.line_content
            content = content.replace("|", "\\|")
            lines.append(f"| {v.file_path} | {v.line_number} | {v.violation_type} | {content} |")
    
    return "\n".join(lines)


def main():
    """主函数"""
    print("=" * 60)
    print("V75.2 入口绕过扫描")
    print("=" * 60)
    
    result = scan_directory(PROJECT_ROOT)
    
    print(f"\n{result.summary}")
    
    if result.violations:
        print("\n违规详情:")
        for v in result.violations:
            print(f"  [{v.violation_type}] {v.file_path}:{v.line_number}")
            print(f"    {v.line_content[:80]}")
    
    # 保存报告
    report_path = PROJECT_ROOT / "scripts" / "v75_2_artifacts" / "ENTRY_BYPASS_SCAN_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = generate_report(result)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n报告已保存: {report_path}")
    
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
