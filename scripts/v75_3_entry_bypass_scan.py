#!/usr/bin/env python3
"""
V75.3 入口绕过扫描 - Hard Fix

扫描所有直接 call_device_tool 入口。
如果发现业务代码绕过 DeviceSerialLane，门禁失败。

V75.3 修复：
- capabilities 目录不再白名单
- 所有端侧动作必须通过串行化器
- 只允许在 sync_executor 回调中调用 call_device_tool
"""

import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# V75.3: 严格限制允许直接调用的模块
ALLOWED_DIRECT_CALL_MODULES = {
    "platform_adapter/device_tool_adapter.py",
    "orchestration/end_side_serial_lanes_v3.py",
    "orchestration/device_serial_call.py",
    "orchestration/end_side_global_serial_executor.py",
}

# 允许直接调用的目录前缀（仅测试和版本脚本）
ALLOWED_DIRECT_CALL_PREFIXES = {
    "tests/",
    "scripts/v75_",
}


@dataclass
class BypassViolation:
    """绕过违规"""
    file_path: str
    line_number: int
    line_content: str
    violation_type: str


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
    
    if rel_path in ALLOWED_DIRECT_CALL_MODULES:
        return True
    
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
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return violations
    
    # V75.3: 找到所有 sync_executor 函数的起始行
    executor_starts = set()
    for i, line in enumerate(lines):
        if 'def sync_executor' in line or 'def executor' in line:
            executor_starts.add(i)
    
    def is_in_sync_executor(line_idx):
        """检查某行是否在 sync_executor 函数内"""
        for start_idx in sorted(executor_starts, reverse=True):
            if start_idx < line_idx:
                start_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
                has_other_def = False
                for j in range(start_idx + 1, line_idx):
                    stripped = lines[j].strip()
                    if stripped.startswith('def ') or stripped.startswith('async def '):
                        current_indent = len(lines[j]) - len(lines[j].lstrip())
                        if current_indent <= start_indent:
                            has_other_def = True
                            break
                if not has_other_def:
                    return True
                break
        return False
    
    for i, line in enumerate(lines, 1):
        line_idx = i - 1
        
        # 检查直接调用 call_device_tool
        if re.search(r'\bcall_device_tool\s*\(', line):
            if 'def call_device_tool' in line or '#' in line.split('call_device_tool')[0]:
                continue
            
            # V75.3: 允许在 sync_executor 函数内调用
            if is_in_sync_executor(line_idx):
                continue
            
            # 允许在 device_serial_call.py 中调用
            if "orchestration/device_serial_call.py" in rel_path:
                continue
            
            # 允许在白名单模块中调用
            if is_allowed_direct_call(file_path):
                continue
            
            violations.append(BypassViolation(
                file_path=rel_path,
                line_number=i,
                line_content=line.strip(),
                violation_type="direct_call"
            ))
        
        # 检查 from tools import call_device_tool
        if re.search(r'from\s+tools\s+import\s+call_device_tool', line):
            if is_in_sync_executor(line_idx):
                continue
            
            if "orchestration/device_serial_call.py" in rel_path:
                continue
            
            if is_allowed_direct_call(file_path):
                continue
            
            violations.append(BypassViolation(
                file_path=rel_path,
                line_number=i,
                line_content=line.strip(),
                violation_type="direct_import"
            ))
        
        # 检查 from platform_adapter.device_tool_adapter import call_device_tool
        if re.search(r'from\s+platform_adapter\.device_tool_adapter\s+import\s+call_device_tool', line):
            if is_in_sync_executor(line_idx):
                continue
            
            if not is_allowed_direct_call(file_path):
                violations.append(BypassViolation(
                    file_path=rel_path,
                    line_number=i,
                    line_content=line.strip(),
                    violation_type="direct_import"
                ))
        
        # 检查 DeviceAction 参数不一致
        if 'DeviceAction(' in line and 'end_side_global_serial_executor.py' not in rel_path:
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
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', 'data')]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                file_violations = scan_file_for_bypass(file_path)
                violations.extend(file_violations)
                files_scanned += 1
    
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
        "# V75.3 入口绕过扫描报告",
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
    print("V75.3 入口绕过扫描 (Hard Fix)")
    print("=" * 60)
    
    result = scan_directory(PROJECT_ROOT)
    
    print(f"\n{result.summary}")
    
    if result.violations:
        print("\n违规详情:")
        for v in result.violations:
            print(f"  [{v.violation_type}] {v.file_path}:{v.line_number}")
            print(f"    {v.line_content[:80]}")
    
    report_path = PROJECT_ROOT / "scripts" / "v75_3_artifacts" / "ENTRY_BYPASS_SCAN_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = generate_report(result)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n报告已保存: {report_path}")
    
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
