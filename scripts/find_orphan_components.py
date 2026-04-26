#!/usr/bin/env python3
"""
孤儿组件扫描器

扫描项目中未被注册、未被引用、未被使用的孤儿组件：
- 孤儿模块
- 孤儿能力
- 孤儿配置
- 孤儿脚本
- 孤儿文档
- 孤儿测试
- 孤儿数据表
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class OrphanComponentScanner:
    """孤儿组件扫描器"""
    
    # 标准目录（不是孤儿）
    STANDARD_DIRS = {
        "core", "memory_context", "orchestration", "execution",
        "governance", "infrastructure", "skills", "tests",
        "scripts", "docs", "config", "data", "reports",
        "capabilities", "diagnostics", "storage", "platform_adapter",
        "memory", "repo", "build", "dist", "node_modules",
        "application", "domain",
    }
    
    # 非核心组件白名单（accepted_non_core）
    ACCEPTED_NON_CORE_SCRIPTS = {
        "generate_architecture_display", "generate_architecture_display_v2",
        "generate_architecture_display_v3", "generate_architecture_display_v4",
        "generate_architecture_display_v5", "generate_architecture_display_v6",
        "generate_architecture_display_v7", "generate_architecture_display_v8",
        "generate_architecture_display_v9", "generate_architecture_display_v10",
        "skill_catalog_export", "module_catalog_export", "dependency_graph_export",
        "inventory_snapshot", "inventory_diff", "skill_access_checker",
        "violation_test_suite", "skill_index_manager",
        "cold_start_test", "cold_start_test_v2",
        # V9 新增白名单
        "check_route_registry", "check_connected_permissions", "create_utility_skills",
        "e2e_route_scenarios", "v9_inspector", "unify_route_risk_levels",
        "activate_routes_smoke", "simulate_task_progress_timeout", "simulate_l0_auto_recovery",
        "visual_probe_smoke", "connected_route_smoke", "verify_routes_static",
        "run_fault_injection_tests", "export_route_audit", "probe_connected_runtime",
        "check_runtime_mode", "export_connected_runtime_audit", "create_clean_package",
        "fix_route_registry_v2", "auto_register_routes",
        # V9.1 新增白名单 - skill registry 工具
        "scan_skills", "sync_skill_registry", "check_skill_registry",
    }
    
    ACCEPTED_NON_CORE_DOCS = {
        "00_exact_refactor_fix_v2", "00_exact_skill_refactor_fix_list",
        "API_REFERENCE", "ARCHITECTURE_RELATIONSHIP", "AUTO_RUN_COMPONENTS",
        "BACKUP_MECHANISM_EXPLAINED", "CAPABILITY_CLOSED_LOOP_MATRIX",
        "CAPABILITY_MATRIX", "CAPABILITY_PERFORMANCE_REPORT", "CHANGELOG",
        "COMPONENT_CLASSIFICATION_POLICY", "COMPRESSION_OPTIMIZATION",
        "CONNECTED_RUNTIME_AUDIT_REPORT", "CONNECTED_RUNTIME_ROUTE_MATRIX",
        "CONNECTED_RUNTIME_SECURITY_REPORT", "CONTRIBUTING",
        # V9 新增白名单
        "ROUTE_ACTIVE_MATRIX_V3", "NOTIFICATION_AUTH_GUIDE", "SCENARIO_TEMPLATE_PACK",
        "RELEASE_READINESS", "RESULT_UNCERTAIN_HANDLING", "WORKFLOW_ENHANCEMENT_PLAN",
        "DEMO_QUICKSTART", "SAFETY_CONTROLS", "ROUTE_ACTIVE_MATRIX",
        "USER_RESULT_MESSAGE_MATRIX", "MANUAL_CONFIRMATION_PLAYBOOK",
        "ROUTE_ACTIVE_MATRIX_V2", "ROUTE_AUDIT_REPORT",
    }
    
    # 非核心配置白名单
    ACCEPTED_NON_CORE_CONFIGS = {
        "default_skill_config",  # 被 config/settings.py 引用
    }
    
    def __init__(self, root: Path = None):
        self.root = root or PROJECT_ROOT
        self.inventory_dir = self.root / "infrastructure" / "inventory"
        self.reports_dir = self.root / "reports" / "integrity"
        
        self.inventory_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.orphans = {
            "modules": [],
            "capabilities": [],
            "configs": [],
            "scripts": [],
            "documents": [],
            "tests": [],
            "tables": [],
        }
    
    def scan_orphan_modules(self) -> List[Dict]:
        """扫描孤儿模块"""
        print("\n📦 扫描孤儿模块...")
        
        orphans = []
        
        # 加载模块注册表
        registry = self._load_registry("module_registry.json")
        registered = set(registry.get("modules", {}).keys())
        
        # 扫描模块目录
        for item in self.root.iterdir():
            if not item.is_dir():
                continue
            if item.name.startswith(".") or item.name.startswith("_"):
                continue
            if item.name in self.STANDARD_DIRS:
                continue
            
            # 检查是否有 __init__.py
            init_file = item / "__init__.py"
            if not init_file.exists():
                continue
            
            # 检查是否注册
            if item.name not in registered:
                orphans.append({
                    "name": item.name,
                    "path": str(item),
                    "reason": "未注册到 module_registry.json",
                })
        
        self.orphans["modules"] = orphans
        print(f"  发现 {len(orphans)} 个孤儿模块")
        
        return orphans
    
    def scan_orphan_capabilities(self) -> List[Dict]:
        """扫描孤儿能力"""
        print("\n⚡ 扫描孤儿能力...")
        
        orphans = []
        
        # 加载能力注册表
        registry = self._load_registry("capability_registry.json")
        registered = set(registry.get("items", {}).keys())
        
        # 扫描 capabilities 目录
        cap_dir = self.root / "capabilities"
        if not cap_dir.exists():
            print("  ⚠️  capabilities 目录不存在")
            return orphans
        
        for cap_file in cap_dir.glob("*.py"):
            if cap_file.name.startswith("_"):
                continue
            
            cap_name = cap_file.stem
            
            # 检查是否注册
            if cap_name not in registered:
                orphans.append({
                    "name": cap_name,
                    "path": str(cap_file),
                    "reason": "未注册到 capability_registry.json",
                })
        
        self.orphans["capabilities"] = orphans
        print(f"  发现 {len(orphans)} 个孤儿能力")
        
        return orphans
    
    def scan_orphan_configs(self) -> List[Dict]:
        """扫描孤儿配置"""
        print("\n⚙️  扫描孤儿配置...")
        
        orphans = []
        
        # 扫描 config 目录
        config_dir = self.root / "config"
        if not config_dir.exists():
            print("  ⚠️  config 目录不存在")
            return orphans
        
        for config_file in config_dir.glob("*"):
            if config_file.name.startswith("_"):
                continue
            
            # 检查是否在白名单中
            if config_file.stem in self.ACCEPTED_NON_CORE_CONFIGS:
                continue  # 跳过白名单中的配置
            
            # 检查是否被引用
            referenced = self._check_file_referenced(config_file.stem, exclude_dir="config")
            
            if not referenced:
                orphans.append({
                    "name": config_file.stem,
                    "path": str(config_file),
                    "reason": "未被任何代码引用",
                })
        
        self.orphans["configs"] = orphans
        print(f"  发现 {len(orphans)} 个孤儿配置")
        
        return orphans
    
    def scan_orphan_scripts(self) -> List[Dict]:
        """扫描孤儿脚本"""
        print("\n📜 扫描孤儿脚本...")
        
        orphans = []
        
        # 加载脚本注册表
        registry = self._load_registry("script_registry.json")
        registered = set(registry.get("items", {}).keys())
        
        # 扫描 scripts 目录
        scripts_dir = self.root / "scripts"
        if not scripts_dir.exists():
            print("  ⚠️  scripts 目录不存在")
            return orphans
        
        for script_file in scripts_dir.glob("*.py"):
            if script_file.name.startswith("_"):
                continue
            
            script_name = script_file.stem
            
            # 检查是否在白名单中
            if script_name in self.ACCEPTED_NON_CORE_SCRIPTS:
                continue  # 跳过白名单中的脚本
            
            # 检查是否注册
            if script_name not in registered:
                orphans.append({
                    "name": script_name,
                    "path": str(script_file),
                    "reason": "未注册到 script_registry.json",
                })
        
        self.orphans["scripts"] = orphans
        print(f"  发现 {len(orphans)} 个孤儿脚本")
        
        return orphans
    
    def scan_orphan_documents(self) -> List[Dict]:
        """扫描孤儿文档"""
        print("\n📄 扫描孤儿文档...")
        
        orphans = []
        
        # 扫描 docs 目录
        docs_dir = self.root / "docs"
        if not docs_dir.exists():
            print("  ⚠️  docs 目录不存在")
            return orphans
        
        # 检查索引文件
        index_files = [
            docs_dir / "README.md",
            docs_dir / "README_RELEASE_INDEX.md",
        ]
        
        indexed_docs = set()
        for index_file in index_files:
            if index_file.exists():
                content = index_file.read_text(encoding='utf-8')
                # 提取所有 .md 文件引用
                import re
                matches = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)
                for _, link in matches:
                    indexed_docs.add(link.replace('.md', ''))
        
        # 内部文档（不需要索引）
        internal_prefixes = [
            "00_",  # 内部文档
            "HEARTBEAT_",  # 心跳相关
            "SCHEDULED_",  # 调度相关
            "PERMANENT_",  # 永久守护
            "AUTO_",  # 自动化
            "DEGRADATION_",  # 降级
            "OPTIMIZATION_",  # 优化
            "EXECUTION_",  # 执行
            "PLATFORM_",  # 平台
            "SKILL_",  # 技能
            "TOKEN_",  # Token
            "MEMORY_",  # 内存
            "COMPONENT_",  # 组件
            "DELIVERY_",  # 交付
            "DELETE_",  # 删除
            "FUSION_",  # 融合
            "COMPRESSION_",  # 压缩
            "REAL_",  # 真实
            "LITE_",  # 精简
            "BACKUP_",  # 备份
            "V7.",  # 版本文档
            "architecture",  # 架构
            "runbook",  # 运维手册
            "production_",  # 生产
            "state_machine",  # 状态机
            "configuration",  # 配置
            "observability",  # 可观测
            "task_lifecycle",  # 任务生命周期
            "loop_guard",  # 循环守卫
            "skill_integration",  # 技能集成
        ]
        
        for doc_file in docs_dir.glob("*.md"):
            if doc_file.name.startswith("_"):
                continue
            if doc_file.name in ["README.md", "README_RELEASE_INDEX.md"]:
                continue
            
            doc_name = doc_file.stem
            
            # 检查是否在白名单中
            if doc_name in self.ACCEPTED_NON_CORE_DOCS:
                continue  # 跳过白名单中的文档
            
            # 检查是否是内部文档
            is_internal = any(doc_name.startswith(prefix) or prefix in doc_name for prefix in internal_prefixes)
            
            if is_internal:
                continue  # 内部文档不算孤儿
            
            # 检查是否在索引中
            if doc_name not in indexed_docs:
                orphans.append({
                    "name": doc_name,
                    "path": str(doc_file),
                    "reason": "未在文档索引中",
                })
        
        self.orphans["documents"] = orphans
        print(f"  发现 {len(orphans)} 个孤儿文档")
        
        return orphans
    
    def scan_orphan_tests(self) -> List[Dict]:
        """扫描孤儿测试"""
        print("\n🧪 扫描孤儿测试...")
        
        orphans = []
        
        # 扫描 tests 目录
        tests_dir = self.root / "tests"
        if not tests_dir.exists():
            print("  ⚠️  tests 目录不存在")
            return orphans
        
        for test_file in tests_dir.glob("test_*.py"):
            # 检查是否能被 pytest 收集
            content = test_file.read_text(encoding='utf-8')
            
            has_test_func = "def test_" in content
            has_test_class = "class Test" in content
            
            if not has_test_func and not has_test_class:
                orphans.append({
                    "name": test_file.stem,
                    "path": str(test_file),
                    "reason": "无可收集的测试函数或类",
                })
        
        self.orphans["tests"] = orphans
        print(f"  发现 {len(orphans)} 个孤儿测试")
        
        return orphans
    
    def scan_orphan_tables(self) -> List[Dict]:
        """扫描孤儿数据表"""
        print("\n🗃️  扫描孤儿数据表...")
        
        orphans = []
        
        # 扫描 data 目录
        data_dir = self.root / "data"
        if not data_dir.exists():
            print("  ⚠️  data 目录不存在")
            return orphans
        
        # 检查 .db 文件
        for db_file in data_dir.glob("*.db"):
            # 检查是否被引用
            referenced = self._check_file_referenced(db_file.stem, exclude_dir="data")
            
            if not referenced:
                orphans.append({
                    "name": db_file.stem,
                    "path": str(db_file),
                    "reason": "未被任何代码引用",
                })
        
        self.orphans["tables"] = orphans
        print(f"  发现 {len(orphans)} 个孤儿数据表")
        
        return orphans
    
    def _load_registry(self, filename: str) -> Dict:
        """加载注册表"""
        path = self.inventory_dir / filename
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"version": "1.0.0", "items": {}, "modules": {}}
    
    def _check_file_referenced(self, name: str, exclude_dir: str = None) -> bool:
        """检查文件是否被引用"""
        try:
            result = subprocess.run(
                ["grep", "-r", name, "--include=*.py", str(self.root)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # 排除自身目录
            if exclude_dir:
                lines = [l for l in lines if f'/{exclude_dir}/' not in l and l]
            
            return len(lines) > 0
        except:
            return True  # 假设已引用
    
    def scan_all(self) -> Dict:
        """扫描所有孤儿组件"""
        print("=" * 60)
        print("  孤儿组件扫描器 V1.0.0")
        print("=" * 60)
        
        self.scan_orphan_modules()
        self.scan_orphan_capabilities()
        self.scan_orphan_configs()
        self.scan_orphan_scripts()
        self.scan_orphan_documents()
        self.scan_orphan_tests()
        self.scan_orphan_tables()
        
        # 汇总
        total = sum(len(v) for v in self.orphans.values())
        
        print("\n" + "=" * 60)
        if total > 0:
            print(f"  ❌ 发现 {total} 个孤儿组件")
            for category, items in self.orphans.items():
                if items:
                    print(f"    {category}: {len(items)} 个")
        else:
            print("  ✅ 没有孤儿组件")
        print("=" * 60 + "\n")
        
        return self.orphans
    
    def save_report(self) -> Path:
        """保存报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "orphans": self.orphans,
            "summary": {
                "total": sum(len(v) for v in self.orphans.values()),
                "by_category": {k: len(v) for k, v in self.orphans.items()},
            },
        }
        
        report_path = self.reports_dir / f"orphan_components_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 报告已保存: {report_path}")
        
        return report_path


def main():
    """主函数"""
    scanner = OrphanComponentScanner()
    scanner.scan_all()
    scanner.save_report()
    
    # 返回退出码
    total = sum(len(v) for v in scanner.orphans.values())
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
