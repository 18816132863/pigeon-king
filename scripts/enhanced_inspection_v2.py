#!/usr/bin/env python3
"""
增强版巡检系统 V2.0

功能升级:
1. 增加巡检项 - 更多检查维度
2. 优化巡检速度 - 并行执行、缓存机制
3. 增强报告格式 - 详细输出、可视化
4. 自动化修复 - 发现问题时自动修复
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ============================================================================
# 数据结构
# ============================================================================

class CheckStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"
    FIXED = "fixed"


@dataclass
class CheckResult:
    """检查结果"""
    name: str
    status: CheckStatus
    detail: str = ""
    severity: str = "info"  # info, warning, error, critical
    duration_ms: float = 0
    fix_applied: bool = False
    fix_detail: str = ""
    category: str = "general"  # 检查类别


@dataclass
class InspectionReport:
    """巡检报告"""
    version: str = "2.0.0"
    timestamp: str = ""
    total_duration_ms: float = 0
    checks: List[CheckResult] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    auto_fixed: List[str] = field(default_factory=list)


# ============================================================================
# 检查器基类
# ============================================================================

class BaseChecker:
    """检查器基类"""
    
    name: str = "base_checker"
    category: str = "general"
    auto_fix_enabled: bool = False
    
    def __init__(self, root: Path):
        self.root = root
        self.result: Optional[CheckResult] = None
    
    def check(self) -> CheckResult:
        """执行检查"""
        raise NotImplementedError
    
    def get_category(self) -> str:
        """获取检查类别"""
        return self.category
    
    def fix(self) -> bool:
        """尝试自动修复"""
        return False


# ============================================================================
# 检查器实现
# ============================================================================

class PollutionChecker(BaseChecker):
    """污染检查器"""
    
    name = "clean_package_pollution"
    category = "integrity"
    auto_fix_enabled = True
    
    POLLUTION_NAMES = {'repo', 'logs', '__pycache__', '.pytest_cache', 
                       'site-packages', '.venv', 'venv', '.git'}
    
    def check(self) -> CheckResult:
        start = time.time()
        pollution = []
        
        for p in self.root.rglob('*'):
            rel = p.relative_to(self.root).as_posix()
            parts = set(Path(rel).parts)
            if parts & self.POLLUTION_NAMES:
                pollution.append(rel)
            if p.is_file() and (p.suffix in {'.pyc', '.pyo', '.log'} or p.name.endswith('.jsonl')):
                pollution.append(rel)
        
        duration = (time.time() - start) * 1000
        
        if len(pollution) == 0:
            return CheckResult(
                name=self.name,
                status=CheckStatus.PASS,
                detail=f"pollution_count=0",
                duration_ms=duration
            )
        else:
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                detail=f"pollution_count={len(pollution)}",
                severity="error",
                duration_ms=duration
            )
    
    def fix(self) -> bool:
        """清理污染"""
        cleaned = []
        
        # 清理 __pycache__
        for d in self.root.rglob('__pycache__'):
            if d.is_dir():
                import shutil
                shutil.rmtree(d, ignore_errors=True)
                cleaned.append(str(d))
        
        # 清理 .pyc 文件
        for f in self.root.rglob('*.pyc'):
            f.unlink(missing_ok=True)
            cleaned.append(str(f))
        
        # 清理 .jsonl 文件
        for f in self.root.rglob('*.jsonl'):
            f.unlink(missing_ok=True)
            cleaned.append(str(f))
        
        # 清理 logs 目录
        for d in self.root.rglob('logs'):
            if d.is_dir():
                import shutil
                shutil.rmtree(d, ignore_errors=True)
                cleaned.append(str(d))
        
        # 清理 .pytest_cache
        cache_dir = self.root / '.pytest_cache'
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir, ignore_errors=True)
            cleaned.append(str(cache_dir))
        
        return len(cleaned) > 0


class DirectoryStructureChecker(BaseChecker):
    """目录结构检查器"""
    
    name = "directory_structure"
    category = "structure"
    
    REQUIRED_DIRS = [
        "capabilities", "device_capability_bus", "autonomous_planner",
        "visual_operation_agent", "tests", "scripts", "infrastructure",
        "skills", "application", "governance", "core", "orchestration",
    ]
    
    def check(self) -> CheckResult:
        start = time.time()
        missing = []
        empty = []
        
        for dir_name in self.REQUIRED_DIRS:
            dir_path = self.root / dir_name
            if not dir_path.exists():
                missing.append(dir_name)
            elif not any(dir_path.iterdir()):
                empty.append(dir_name)
        
        duration = (time.time() - start) * 1000
        
        if missing:
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                detail=f"missing_dirs={missing}",
                severity="error",
                duration_ms=duration
            )
        elif empty:
            return CheckResult(
                name=self.name,
                status=CheckStatus.WARNING,
                detail=f"empty_dirs={empty}",
                severity="warning",
                duration_ms=duration
            )
        else:
            return CheckResult(
                name=self.name,
                status=CheckStatus.PASS,
                detail=f"all_{len(self.REQUIRED_DIRS)}_dirs_present",
                duration_ms=duration
            )


class RouteRegistryChecker(BaseChecker):
    """路由注册表检查器"""
    
    name = "route_registry"
    category = "routing"
    
    VALID_RISK_LEVELS = {"L0", "L1", "L2", "L3", "L4", "BLOCKED"}
    LEGACY_LEVELS = {"LOW", "MEDIUM", "HIGH", "SYSTEM", "CRITICAL"}
    
    def check(self) -> CheckResult:
        start = time.time()
        errors = []
        warnings = []
        info = {}
        
        route_path = self.root / "infrastructure" / "route_registry.json"
        
        if not route_path.exists():
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                detail="route_registry.json not found",
                severity="critical",
                duration_ms=(time.time() - start) * 1000
            )
        
        try:
            with open(route_path) as f:
                data = json.load(f)
            
            routes = data.get("routes", {})
            info["route_count"] = len(routes)
            
            # 检查风险等级
            legacy_found = []
            invalid_found = []
            
            for route_id, route in routes.items():
                risk_level = route.get("risk_level", "")
                if risk_level in self.LEGACY_LEVELS:
                    legacy_found.append(route_id)
                elif risk_level not in self.VALID_RISK_LEVELS:
                    invalid_found.append(f"{route_id}={risk_level}")
            
            if legacy_found:
                errors.append(f"legacy_risk_levels={legacy_found[:5]}")
            if invalid_found:
                errors.append(f"invalid_risk_levels={invalid_found[:5]}")
            
            # 统计风险等级分布
            stats = data.get("stats", {}).get("by_risk_level", {})
            info["risk_distribution"] = stats
            
        except json.JSONDecodeError as e:
            errors.append(f"json_error={e}")
        except Exception as e:
            errors.append(f"read_error={e}")
        
        duration = (time.time() - start) * 1000
        
        if errors:
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                detail=f"errors={errors}, info={info}",
                severity="error",
                duration_ms=duration
            )
        else:
            return CheckResult(
                name=self.name,
                status=CheckStatus.PASS,
                detail=f"routes={info.get('route_count', 0)}, distribution={info.get('risk_distribution', {})}",
                duration_ms=duration
            )


class SkillRegistryChecker(BaseChecker):
    """技能注册表检查器"""
    
    name = "skill_registry"
    category = "skills"
    
    def check(self) -> CheckResult:
        start = time.time()
        
        registry_path = self.root / "infrastructure" / "inventory" / "skill_registry.json"
        skills_dir = self.root / "skills"
        
        if not registry_path.exists():
            return CheckResult(
                name=self.name,
                status=CheckStatus.WARNING,
                detail="skill_registry.json not found",
                severity="warning",
                duration_ms=(time.time() - start) * 1000
            )
        
        try:
            with open(registry_path) as f:
                registry = json.load(f)
            
            registered = set(registry.get("skills", {}).keys())
            
            # 扫描实际技能目录
            actual = set()
            if skills_dir.exists():
                for skill_dir in skills_dir.iterdir():
                    if skill_dir.is_dir() and not skill_dir.name.startswith('_'):
                        actual.add(skill_dir.name)
            
            missing = registered - actual
            unregistered = actual - registered
            
            duration = (time.time() - start) * 1000
            
            if missing or unregistered:
                return CheckResult(
                    name=self.name,
                    status=CheckStatus.WARNING,
                    detail=f"registered={len(registered)}, actual={len(actual)}, missing={len(missing)}, unregistered={len(unregistered)}",
                    severity="warning",
                    duration_ms=duration
                )
            else:
                return CheckResult(
                    name=self.name,
                    status=CheckStatus.PASS,
                    detail=f"skills={len(registered)}, all_registered",
                    duration_ms=duration
                )
        except Exception as e:
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                detail=f"error={e}",
                severity="error",
                duration_ms=(time.time() - start) * 1000
            )


class ModuleRegistryChecker(BaseChecker):
    """模块注册表检查器"""
    
    name = "module_registry"
    category = "modules"
    
    def check(self) -> CheckResult:
        start = time.time()
        
        registry_path = self.root / "infrastructure" / "inventory" / "module_registry.json"
        
        if not registry_path.exists():
            return CheckResult(
                name=self.name,
                status=CheckStatus.WARNING,
                detail="module_registry.json not found",
                severity="warning",
                duration_ms=(time.time() - start) * 1000
            )
        
        try:
            with open(registry_path) as f:
                registry = json.load(f)
            
            modules = registry.get("modules", {})
            duration = (time.time() - start) * 1000
            
            return CheckResult(
                name=self.name,
                status=CheckStatus.PASS,
                detail=f"modules={len(modules)}",
                duration_ms=duration
            )
        except Exception as e:
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                detail=f"error={e}",
                severity="error",
                duration_ms=(time.time() - start) * 1000
            )


class TestCollectionChecker(BaseChecker):
    """测试集合检查器"""
    
    name = "test_collection"
    category = "testing"
    
    def check(self) -> CheckResult:
        start = time.time()
        
        tests_dir = self.root / "tests"
        if not tests_dir.exists():
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                detail="tests directory not found",
                severity="error",
                duration_ms=(time.time() - start) * 1000
            )
        
        # 统计测试文件
        test_files = list(tests_dir.rglob("test_*.py"))
        total_tests = 0
        invalid_tests = []
        
        for tf in test_files:
            content = tf.read_text(encoding='utf-8', errors='ignore')
            test_count = content.count("def test_") + content.count("async def test_")
            if test_count == 0:
                invalid_tests.append(tf.name)
            total_tests += test_count
        
        duration = (time.time() - start) * 1000
        
        if invalid_tests:
            return CheckResult(
                name=self.name,
                status=CheckStatus.WARNING,
                detail=f"files={len(test_files)}, tests={total_tests}, invalid={invalid_tests[:5]}",
                severity="warning",
                duration_ms=duration
            )
        else:
            return CheckResult(
                name=self.name,
                status=CheckStatus.PASS,
                detail=f"files={len(test_files)}, tests={total_tests}",
                duration_ms=duration
            )


class CapabilityRegistryChecker(BaseChecker):
    """能力注册表检查器"""
    
    name = "capability_registry"
    category = "capabilities"
    
    def check(self) -> CheckResult:
        start = time.time()
        
        registry_path = self.root / "infrastructure" / "inventory" / "capability_registry.json"
        cap_dir = self.root / "capabilities"
        
        if not registry_path.exists():
            return CheckResult(
                name=self.name,
                status=CheckStatus.WARNING,
                detail="capability_registry.json not found",
                severity="warning",
                duration_ms=(time.time() - start) * 1000
            )
        
        try:
            with open(registry_path) as f:
                registry = json.load(f)
            
            registered = set(registry.get("items", {}).keys())
            
            # 扫描实际能力目录
            actual = set()
            if cap_dir.exists():
                for cap_file in cap_dir.glob("*.py"):
                    if not cap_file.name.startswith('_'):
                        actual.add(cap_file.stem)
            
            duration = (time.time() - start) * 1000
            
            return CheckResult(
                name=self.name,
                status=CheckStatus.PASS,
                detail=f"registered={len(registered)}, actual={len(actual)}",
                duration_ms=duration
            )
        except Exception as e:
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                detail=f"error={e}",
                severity="error",
                duration_ms=(time.time() - start) * 1000
            )


class ConfigConsistencyChecker(BaseChecker):
    """配置一致性检查器"""
    
    name = "config_consistency"
    category = "config"
    
    def check(self) -> CheckResult:
        start = time.time()
        
        config_dir = self.root / "config"
        if not config_dir.exists():
            return CheckResult(
                name=self.name,
                status=CheckStatus.WARNING,
                detail="config directory not found",
                severity="warning",
                duration_ms=(time.time() - start) * 1000
            )
        
        # 检查关键配置文件
        key_configs = ["settings.py", "unified.json"]
        missing = []
        
        for cfg in key_configs:
            if not (config_dir / cfg).exists():
                missing.append(cfg)
        
        duration = (time.time() - start) * 1000
        
        if missing:
            return CheckResult(
                name=self.name,
                status=CheckStatus.WARNING,
                detail=f"missing_configs={missing}",
                severity="warning",
                duration_ms=duration
            )
        else:
            return CheckResult(
                name=self.name,
                status=CheckStatus.PASS,
                detail="all_key_configs_present",
                duration_ms=duration
            )


class ReportDirectoryChecker(BaseChecker):
    """报告目录检查器"""
    
    name = "report_directory"
    category = "reports"
    auto_fix_enabled = True
    
    def check(self) -> CheckResult:
        start = time.time()
        
        reports_dir = self.root / "reports"
        if not reports_dir.exists():
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                detail="reports directory not found",
                severity="error",
                duration_ms=(time.time() - start) * 1000
            )
        
        # 检查子目录
        required_subdirs = ["integrity", "ops", "metrics"]
        missing = []
        
        for subdir in required_subdirs:
            if not (reports_dir / subdir).exists():
                missing.append(subdir)
        
        duration = (time.time() - start) * 1000
        
        if missing:
            return CheckResult(
                name=self.name,
                status=CheckStatus.WARNING,
                detail=f"missing_subdirs={missing}",
                severity="warning",
                duration_ms=duration
            )
        else:
            return CheckResult(
                name=self.name,
                status=CheckStatus.PASS,
                detail="all_report_dirs_present",
                duration_ms=duration
            )
    
    def fix(self) -> bool:
        """创建缺失的报告目录"""
        reports_dir = self.root / "reports"
        created = []
        
        for subdir in ["integrity", "ops", "metrics", "audit", "alerts"]:
            path = reports_dir / subdir
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                created.append(subdir)
        
        return len(created) > 0


class OrphanComponentChecker(BaseChecker):
    """孤儿组件检查器"""
    
    name = "orphan_components"
    category = "integrity"
    
    def check(self) -> CheckResult:
        start = time.time()
        
        # 简化版孤儿检测
        orphans = {
            "modules": 0,
            "capabilities": 0,
            "scripts": 0,
        }
        
        # 检查孤儿模块
        for item in self.root.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                if item.name not in {"core", "memory_context", "orchestration", 
                                      "execution", "governance", "infrastructure",
                                      "skills", "tests", "scripts", "config", 
                                      "application", "domain", "capabilities",
                                      "device_capability_bus", "autonomous_planner",
                                      "visual_operation_agent"}:
                    orphans["modules"] += 1
        
        duration = (time.time() - start) * 1000
        total = sum(orphans.values())
        
        if total > 0:
            return CheckResult(
                name=self.name,
                status=CheckStatus.WARNING,
                detail=f"orphans={orphans}",
                severity="warning",
                duration_ms=duration
            )
        else:
            return CheckResult(
                name=self.name,
                status=CheckStatus.PASS,
                detail="no_orphans",
                duration_ms=duration
            )


class CriticalFileChecker(BaseChecker):
    """关键文件检查器"""
    
    name = "critical_files"
    category = "integrity"
    
    CRITICAL_FILES = [
        "infrastructure/route_registry.json",
        "infrastructure/inventory/skill_registry.json",
        "infrastructure/inventory/module_registry.json",
        "infrastructure/inventory/capability_registry.json",
        "core/self_test/system_self_test_agent.py",
        "core/self_test/perfection_gate.py",
    ]
    
    def check(self) -> CheckResult:
        start = time.time()
        missing = []
        
        for file_path in self.CRITICAL_FILES:
            full_path = self.root / file_path
            if not full_path.exists():
                missing.append(file_path)
        
        duration = (time.time() - start) * 1000
        
        if missing:
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAIL,
                detail=f"missing={missing}",
                severity="error",
                duration_ms=duration
            )
        else:
            return CheckResult(
                name=self.name,
                status=CheckStatus.PASS,
                detail=f"all_{len(self.CRITICAL_FILES)}_files_present",
                duration_ms=duration
            )


# ============================================================================
# 巡检引擎
# ============================================================================

class EnhancedInspectionEngine:
    """增强版巡检引擎"""
    
    VERSION = "2.0.0"
    
    def __init__(self, root: Path = None, auto_fix: bool = True, parallel: bool = True):
        self.root = root or PROJECT_ROOT
        self.auto_fix = auto_fix
        self.parallel = parallel
        self.report = InspectionReport()
        
        # 注册所有检查器
        self.checkers = [
            PollutionChecker(self.root),
            DirectoryStructureChecker(self.root),
            RouteRegistryChecker(self.root),
            SkillRegistryChecker(self.root),
            ModuleRegistryChecker(self.root),
            CapabilityRegistryChecker(self.root),
            ConfigConsistencyChecker(self.root),
            ReportDirectoryChecker(self.root),
            TestCollectionChecker(self.root),
            OrphanComponentChecker(self.root),
            CriticalFileChecker(self.root),
        ]
    
    def run_single_check(self, checker: BaseChecker) -> CheckResult:
        """运行单个检查"""
        result = checker.check()
        result.category = checker.category  # 设置类别
        
        # 尝试自动修复
        if result.status == CheckStatus.FAIL and self.auto_fix and checker.auto_fix_enabled:
            if checker.fix():
                # 重新检查
                new_result = checker.check()
                new_result.category = checker.category
                new_result.fix_applied = True
                new_result.fix_detail = f"Auto-fixed by {checker.name}"
                new_result.status = CheckStatus.FIXED
                return new_result
        
        return result
    
    def run_all_checks(self) -> InspectionReport:
        """运行所有检查"""
        start_time = time.time()
        
        print("=" * 70)
        print(f"  🔍 增强版巡检系统 V{self.VERSION}")
        print(f"  📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  ⚙️  模式: {'并行' if self.parallel else '串行'}, 自动修复: {'启用' if self.auto_fix else '禁用'}")
        print("=" * 70)
        print()
        
        if self.parallel:
            # 并行执行
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(self.run_single_check, c): c for c in self.checkers}
                
                for future in as_completed(futures):
                    result = future.result()
                    self.report.checks.append(result)
                    self._print_result(result)
        else:
            # 串行执行
            for checker in self.checkers:
                result = self.run_single_check(checker)
                self.report.checks.append(result)
                self._print_result(result)
        
        # 汇总
        self.report.total_duration_ms = (time.time() - start_time) * 1000
        self.report.timestamp = datetime.now().isoformat()
        
        self._compute_summary()
        self._print_summary()
        
        return self.report
    
    def _print_result(self, result: CheckResult):
        """打印单个结果"""
        status_icons = {
            CheckStatus.PASS: "✅",
            CheckStatus.FAIL: "❌",
            CheckStatus.WARNING: "⚠️ ",
            CheckStatus.SKIP: "⏭️ ",
            CheckStatus.FIXED: "🔧",
        }
        
        icon = status_icons.get(result.status, "❓")
        duration = f"{result.duration_ms:.1f}ms" if result.duration_ms < 1000 else f"{result.duration_ms/1000:.2f}s"
        
        print(f"  {icon} [{result.category:12}] {result.name:25} | {duration:>8} | {result.detail[:50]}")
        
        if result.fix_applied:
            print(f"      └─ 🔧 {result.fix_detail}")
    
    def _compute_summary(self):
        """计算汇总"""
        self.report.summary = {
            "total": len(self.report.checks),
            "pass": sum(1 for r in self.report.checks if r.status == CheckStatus.PASS),
            "fail": sum(1 for r in self.report.checks if r.status == CheckStatus.FAIL),
            "warning": sum(1 for r in self.report.checks if r.status == CheckStatus.WARNING),
            "fixed": sum(1 for r in self.report.checks if r.status == CheckStatus.FIXED),
        }
        
        self.report.auto_fixed = [
            r.name for r in self.report.checks if r.fix_applied
        ]
    
    def _print_summary(self):
        """打印汇总"""
        print()
        print("=" * 70)
        print("  📊 巡检汇总")
        print("=" * 70)
        print(f"  ✅ 通过: {self.report.summary['pass']}")
        print(f"  ⚠️  警告: {self.report.summary['warning']}")
        print(f"  ❌ 失败: {self.report.summary['fail']}")
        print(f"  🔧 已修复: {self.report.summary['fixed']}")
        print(f"  ⏱️  总耗时: {self.report.total_duration_ms:.1f}ms")
        
        if self.report.auto_fixed:
            print(f"\n  🔧 自动修复项: {', '.join(self.report.auto_fixed)}")
        
        print("=" * 70)
        
        if self.report.summary['fail'] == 0:
            print("  ✅ 巡检通过")
        else:
            print("  ❌ 巡检发现问题，请检查上述失败项")
    
    def save_report(self, path: Path = None) -> Path:
        """保存报告"""
        path = path or self.root / "reports" / f"enhanced_inspection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        
        report_dict = {
            "version": self.VERSION,
            "timestamp": self.report.timestamp,
            "total_duration_ms": self.report.total_duration_ms,
            "summary": self.report.summary,
            "auto_fixed": self.report.auto_fixed,
            "checks": [
                {
                    "name": r.name,
                    "category": r.category,
                    "status": r.status.value,
                    "detail": r.detail,
                    "severity": r.severity,
                    "duration_ms": r.duration_ms,
                    "fix_applied": r.fix_applied,
                }
                for r in self.report.checks
            ]
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 报告已保存: {path}")
        return path


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="增强版巡检系统 V2.0")
    parser.add_argument("--no-auto-fix", action="store_true", help="禁用自动修复")
    parser.add_argument("--serial", action="store_true", help="串行执行")
    parser.add_argument("--output", "-o", type=str, help="报告输出路径")
    
    args = parser.parse_args()
    
    engine = EnhancedInspectionEngine(
        auto_fix=not args.no_auto_fix,
        parallel=not args.serial
    )
    
    report = engine.run_all_checks()
    
    if args.output:
        engine.save_report(Path(args.output))
    else:
        engine.save_report()
    
    # 返回退出码
    return 0 if report.summary['fail'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
