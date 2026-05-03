#!/usr/bin/env python3
"""
统一巡检器 V11.0 — V99 融合升级版

V10 → V11 升级内容：
  1-10. (同上)
  V11.1.0 新增：
  11. 新增重复文件检查（同名同内容）
  12. 新增空壳转发文件检查（仅 import 转发语句）
  13. 新增未引用文件检查（.py 未被任何其他模块 import）
  14. 新增超大文件检查（>5000行）
  V11.2.0 新增：
  15. 新增 Commit Barrier 探针检查（V104.3 集成，覆盖 6 类提交动作阻塞 + 非阻塞动作分类 + 模块完整性）
  16. 新增人格真实性一致性检查（V103.1 集成，覆盖 AGENTS.md 安全规则/IDENTITY.md 真实性表/环境变量安全）
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# ── 继承 openclaw.json 的环境变量（子进程不自动继承 agents.defaults.env） ──
def _inherit_openclaw_env():
    """读取 openclaw.json 中的 agents.defaults.env 并设置到 os.environ。"""
    try:
        conf_path = Path.home() / ".openclaw" / "openclaw.json"
        if conf_path.exists():
            conf = json.loads(conf_path.read_text(encoding="utf-8"))
            env_vars = conf.get("agents", {}).get("defaults", {}).get("env", {})
            for k, v in env_vars.items():
                os.environ.setdefault(k, v)
    except Exception:
        pass  # 静默失败，不影响巡检主逻辑

_inherit_openclaw_env()
# ────────────────────────────────────────

MAX_WORKERS = 8
DEFAULT_TIMEOUT = 30
VERSION = "V11.2.0"


def get_project_root() -> Path:
    current = Path(__file__).resolve().parent.parent
    if (current / "core" / "llm").exists():
        return current
    return Path(__file__).resolve().parent.parent


def check_dir_exists(root: Path, path: str) -> Dict:
    full = root / path
    return {"path": path, "exists": full.is_dir(), "file_count": len(list(full.rglob("*.py"))) if full.is_dir() else 0}


def check_file_exists(root: Path, path: str) -> Dict:
    full = root / path
    return {"path": path, "exists": full.exists(), "size": full.stat().st_size if full.exists() else 0}


def check_json_valid(root: Path, path: str) -> Dict:
    full = root / path
    result = {"path": path, "exists": full.exists(), "valid": False, "error": None}
    if full.exists():
        try:
            with open(full) as f:
                json.load(f)
            result["valid"] = True
        except Exception as e:
            result["error"] = str(e)
    return result


def get_system_stats() -> Dict:
    stats = {}
    try:
        import psutil
        stats["cpu_percent"] = psutil.cpu_percent(interval=1)
        stats["memory_percent"] = psutil.virtual_memory().percent
        stats["disk_percent"] = psutil.disk_usage("/").percent
    except ImportError:
        try:
            stats["disk_percent"] = float(subprocess.run(["df", "/"], capture_output=True, text=True).stdout.split("\n")[1].split()[4].replace("%", ""))
        except Exception:
            stats["disk_percent"] = 0
        try:
            mem = subprocess.run(["free"], capture_output=True, text=True).stdout.split("\n")[1].split()
            total, used = float(mem[1]), float(mem[2])
            stats["memory_percent"] = round(used / total * 100, 1)
        except Exception:
            stats["memory_percent"] = 0
    return stats


class V11Inspector:
    def __init__(self, root: Optional[Path] = None):
        self.root = root or get_project_root()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.checks: List[Dict] = []
        self.system_stats = get_system_stats()

    # ── 0. 系统状态 ──
    def check_system(self):
        print("\n" + "=" * 60)
        print("🖥️  系统状态")
        print("=" * 60)
        if self.system_stats.get("disk_percent", 0) > 90:
            self.warnings.append(f"磁盘使用率 {self.system_stats['disk_percent']}% > 90%")
        print(f"   磁盘: {self.system_stats.get('disk_percent', '?')}%")
        print(f"   内存: {self.system_stats.get('memory_percent', '?')}%")
        try:
            gw = subprocess.run(["openclaw", "gateway", "status"], capture_output=True, text=True, timeout=10)
            out = gw.stdout.strip()
            if not out:
                print("   ℹ️  Gateway: 沙箱中未启动守护进程")
            elif "ok" in out.lower() or "running" in out.lower():
                print("   ✅ Gateway: running")
            else:
                print("   ⚠️  Gateway:", out[:50])
        except Exception:
            print("   ℹ️  Gateway: 无法检测（沙箱环境）")
        health_pid = None
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
            for line in result.stdout.split("\n"):
                if "health_watch.py" in line and "grep" not in line:
                    parts = line.split()
                    if len(parts) > 1:
                        health_pid = parts[1]
                    break
        except Exception:
            pass
        if health_pid:
            print(f"   ✅ 健康监控: 运行中 (PID {health_pid})")
        else:
            print("   ⚠️  健康监控: 未运行")
            self.warnings.append("健康监控守护进程未运行")
        return True

    # ── 1. 六层架构 ──
    def check_layers(self):
        print("\n" + "=" * 60)
        print("🏗️  六层架构完整性")
        print("=" * 60)
        layers = {
            "L1 Core": "core",
            "L2 Memory Context": "memory_context",
            "L3 Orchestration": "orchestration",
            "L4 Execution": "execution",
            "L5 Governance": "governance",
            "L6 Infrastructure": "infrastructure",
        }
        all_pass = True
        for name, path in layers.items():
            d = check_dir_exists(self.root, path)
            if d["exists"]:
                print(f"   ✅ {name} ({path}/) — {d['file_count']} .py")
            else:
                print(f"   ❌ {name} ({path}/) — 缺失")
                self.errors.append(f"六层架构目录缺失: {path}")
                all_pass = False
        return all_pass

    # ── 2. V99 目录融合完整性 ──
    def check_v99_fusion(self):
        print("\n" + "=" * 60)
        print("🔄 V99 目录融合完整性")
        print("=" * 60)
        all_pass = True

        # 2a. 根目录清理
        init_removed = not (self.root / "__init__.py").exists()
        skill_archived = not (self.root / "SKILL.md").exists()
        print(f"   {'✅' if init_removed else '❌'} 根目录 __init__.py 已删除")
        print(f"   {'✅' if skill_archived else '❌'} 根目录 SKILL.md 已归档")
        if not init_removed:
            self.errors.append("根目录 __init__.py 残留")
            all_pass = False
        if not skill_archived:
            self.warnings.append("根目录 SKILL.md 未归档")

        # 2b. agent_kernel 已迁移到 orchestration/agent_kernel
        ak_migrated = (self.root / "orchestration" / "agent_kernel").exists()
        print(f"   {'✅' if ak_migrated else '❌'} agent_kernel → orchestration/agent_kernel/ 已迁移")
        if not ak_migrated:
            self.errors.append("orchestration/agent_kernel/ 不存在（迁移失败）")
            all_pass = False
        else:
            ak_files = len(list((self.root / "orchestration" / "agent_kernel").rglob("*.py")))
            print(f"      orchestration/agent_kernel/: {ak_files} .py 文件")

        # 2c. V99 报告存在
        v99_reports = [
            "reports/V99_DIRECTORY_FUSION_AND_CLEANUP_GATE.json",
            "reports/V99_LAYER_MAPPING_REPORT.json",
            "reports/V99_ARCHIVE_CANDIDATES_REPORT.json",
            "reports/V99_IMPORT_RISK_REPORT.json",
        ]
        v99_pass = True
        for p in v99_reports:
            r = check_json_valid(self.root, p)
            if r["valid"]:
                print(f"   ✅ {p.split('/')[-1]}")
            else:
                print(f"   ⚠️  {p.split('/')[-1]} — {'不存在' if not r['exists'] else '无效'}")
                self.warnings.append(f"V99 报告缺失: {p}")
                v99_pass = False
        if not v99_pass:
            all_pass = False

        # 2d. archive/ 脚本归档
        archive_scripts = self.root / "archive" / "scripts" / "vintage"
        if archive_scripts.is_dir():
            ac = len(list(archive_scripts.glob("*.py")))
            print(f"   ✅ archive/scripts/vintage/: {ac} 归档脚本")
        else:
            print(f"   ⚠️  archive/scripts/vintage/ 不存在")
            self.warnings.append("archive/scripts/vintage/ 目录不存在")

        # 2e. 低风险目录迁移检查（V99 后实际位置）
        domain_dir = check_dir_exists(self.root, "domain")
        eval_dir = check_dir_exists(self.root, "evaluation")
        domain_migrated = check_dir_exists(self.root, "core/domain")
        eval_migrated = check_dir_exists(self.root, "governance/evaluation")
        print(f"   {'✅' if domain_migrated['exists'] else '⚠️'} domain/ → core/domain/ ({domain_migrated['file_count']} 文件, 映射 L1 Core)")
        print(f"   {'✅' if eval_migrated['exists'] else '⚠️'} evaluation/ → governance/evaluation/ ({eval_migrated['file_count']} 文件, 映射 L5 Governance)")
        if domain_dir['exists']:
            self.warnings.append("domain/ 旧目录仍在，应清理")
        if eval_dir['exists']:
            self.warnings.append("evaluation/ 旧目录仍在，应清理")

        return all_pass

    # ── 3. 基础设施模块检查 ──
    def check_infrastructure_modules(self):
        print("\n" + "=" * 60)
        print("🔧 基础设施模块检查")
        print("=" * 60)
        modules = [
            ("safe_jsonable", "infrastructure/safe_jsonable.py"),
            ("mainline_hook", "infrastructure/mainline_hook.py"),
            ("message_hook_bootstrap", "infrastructure/message_hook_bootstrap.py"),
        ]
        all_pass = True
        for name, path in modules:
            r = check_file_exists(self.root, path)
            if r["exists"]:
                print(f"   ✅ {name} ({r['size']} bytes)")
            else:
                print(f"   ❌ {name} — 缺失")
                self.errors.append(f"基础设施模块缺失: {path}")
                all_pass = False
        return all_pass

    # ── 4. V76-V85 模块（精简版） ──
    def check_v85_modules(self):
        print("\n" + "=" * 60)
        print("🔬 V76-V85 关键模块检查")
        print("=" * 60)
        key_modules = [
            ("宪法运行时", "governance/constitutional_runtime/operating_constitution.py"),
            ("前置门控", "governance/constitutional_runtime/preflight_gate.py"),
            ("红队安全", "governance/red_team_safety/circuit_breakers.py"),
            ("权限租约", "governance/access_control/permission_lease.py"),
            ("执行运行时", "infrastructure/execution_runtime/dry_run_mirror.py"),
            ("审计治理", "infrastructure/audit_governance/audit_ledger.py"),
            ("自主任务运行时", "orchestration/autonomous_task_runtime/autonomous_runtime_kernel.py"),
            ("最终发布", "orchestration/final_pending_release/v85_final_kernel.py"),
            ("自演化", "orchestration/self_evolving_pending_os/self_evolving_kernel.py"),
        ]
        passed = sum(1 for _, p in key_modules if (self.root / p).exists())
        for label, path in key_modules:
            exists = (self.root / path).exists()
            print(f"   {'✅' if exists else '❌'} {label}")
        print(f"\n   关键模块: {passed}/{len(key_modules)} 通过")
        return passed == len(key_modules)

    # ── 5. 知识图谱检查 ──
    def check_knowledge_graph(self):
        print("\n" + "=" * 60)
        print("🧠 知识图谱模块检查")
        print("=" * 60)
        modules = [
            ("PersonalKnowledgeGraphV5", "memory_context/personal_knowledge_graph_v5.py"),
            ("MemoryNodeV5", "memory_context/personal_knowledge_graph_v5.py"),
        ]
        all_pass = True
        for name, path in modules:
            r = check_file_exists(self.root, path)
            if r["exists"]:
                print(f"   ✅ {name} 在 {path}")
            else:
                print(f"   ❌ {name} — 缺失")
                self.errors.append(f"知识图谱模块缺失: {path}")
                all_pass = False
        return all_pass

    # ── 6. V90-V99 门报告检查 ──
    def check_gate_reports(self):
        print("\n" + "=" * 60)
        print("🎯 V90-V99 门报告检查")
        print("=" * 60)
        v90_reports = [
            "reports/V95_2_ALL_CHAIN_COVERAGE_GATE.json",
            "reports/V96_FAILURE_RECOVERY_AND_STABILITY_GATE.json",
            "reports/V96_FAILURE_INJECTION_LEDGER.json",
            "reports/V97_LONG_RUN_STABILITY_GATE.json",
            "reports/V97_STABILITY_RUN_LEDGER.json",
            "reports/V98_1_MAINLINE_HOOK_RUNTIME_GATE.json",
            "reports/V99_1_OPS_DASHBOARD.html",
            "reports/V99_DIRECTORY_FUSION_AND_CLEANUP_GATE.json",
        ]
        passed = 0
        failed = 0
        for p in v90_reports:
            r = check_file_exists(self.root, p) if p.endswith((".html", ".txt")) else check_json_valid(self.root, p)
            if isinstance(r, dict):
                ok = r.get("valid", False) if "valid" in r else r.get("exists", False)
            else:
                ok = r
            if ok:
                print(f"   ✅ {p.split('/')[-1]}")
                passed += 1
            else:
                print(f"   ⚠️  {p.split('/')[-1]} — {'不存在' if not r.get('exists', True) else '无效'}")
                self.warnings.append(f"报告缺失: {p}")
                failed += 1
        print(f"\n   报告: {passed}/{passed + failed} 有效")
        return failed == 0

    # ── 7. LLM 引擎 ──
    def check_llm_engine(self):
        print("\n" + "=" * 60)
        print("🤖 LLM 引擎检查")
        print("=" * 60)
        checks_list = [
            ("core.llm.model_registry", "ModelRegistry"),
            ("core.llm.model_router", "route_message"),
            ("core.llm.model_discovery", "discover_and_register"),
        ]
        passed = 0
        sys.path.insert(0, str(self.root))
        check_dir = self.root
        for module_name, cls_name in checks_list:
            try:
                import importlib
                mod = importlib.import_module(module_name)
                has = hasattr(mod, cls_name)
            except Exception:
                has = False
            if has:
                print(f"   ✅ {module_name}.{cls_name}")
                passed += 1
            else:
                print(f"   ⚠️  {module_name}.{cls_name} — import 失败")
                self.warnings.append(f"LLM 模块 import 失败: {module_name}.{cls_name}")
        print(f"\n   LLM 引擎: {passed}/{len(checks_list)} 通过")
        return passed == len(checks_list)

    # ── 8. 重复/冗余文件检查 ──
    def check_duplicates_and_redundancy(self):
        print("\n" + "=" * 60)
        print("♻️  重复与冗余文件检查")
        print("=" * 60)
        all_pass = True

        EXCLUDE_DIRS = {
            '__pycache__', '.git', '.github', 'node_modules', 'repo',
            'releases', 'skills', 'archive',
            '.backup_20260501_0102', '.clawhub', '.openclaw',
            '.knowledge_graph_state', '.offline_state', '.preference_evolution_state',
            '.pytest_cache', '.repair_state', '.self_evolution_ops_state',
            '.self_evolution_state', '.v92_offline_state', '.v93_state', '.v95_2_state',
            '.v96_state', '.v97_state', '.v98_hook_state', '.v98_state', '.v100_state',
        }
        from collections import defaultdict

        def in_excluded(p):
            return any(d in EXCLUDE_DIRS for d in p.parts)

        # 8a. 同名同内容重复文件
        print("\n   📋 8a. 同名同内容重复文件")
        name_map = defaultdict(list)
        dupes = 0
        for p in sorted(self.root.rglob("*.py")):
            if in_excluded(p):
                continue
            if p.name == "__init__.py":
                continue
            try:
                sz = p.stat().st_size
                name_map[p.name].append((p, sz))
            except Exception:
                pass

        for name, items in sorted(name_map.items()):
            if len(items) <= 1:
                continue
            sizes = set(i[1] for i in items)
            if len(sizes) == 1:
                # Same size — check full hash
                hash_map = defaultdict(list)
                for path, sz in items:
                    try:
                        fh = hashlib.md5(path.read_bytes()).hexdigest()
                    except Exception:
                        fh = ""
                    hash_map[fh].append(str(path.relative_to(self.root)))
                for fh, paths in hash_map.items():
                    if len(paths) > 1:
                        dupes += len(paths) - 1
                        print(f"      🔁 {name} ({len(paths)} copies):")
                        for pa in paths[:5]:
                            print(f"          {pa}")
                        if len(paths) > 5:
                            print(f"          ... +{len(paths)-5} more")

        if dupes == 0:
            print("      ✅ 无重复文件")
        else:
            msg = f"发现 {dupes} 组重复文件"
            print(f"      ⚠️ {msg}")
            self.warnings.append(msg)
            all_pass = False

        # 8b. 空壳文件（仅包含 import 转发语句）
        print("\n   📋 8b. 空壳转发文件检查")
        stub_count = 0
        for p in sorted(self.root.rglob("*.py")):
            if in_excluded(p):
                continue
            if p.name == "__init__.py":
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore").strip()
                lines = [l.strip() for l in text.split("\n") if l.strip() and not l.strip().startswith("#")]
                if len(lines) == 1 and "import" in lines[0]:
                    stub_count += 1
                    if stub_count <= 5:
                        print(f"      ⚠️ {p.relative_to(self.root)}")
                elif len(lines) <= 4 and all("import" in l or l.startswith("#") for l in lines):
                    # Could be a multi-comment + one import line stub
                    import_lines = [l for l in lines if "import" in l]
                    if len(import_lines) == 1:
                        stub_count += 1
                        if stub_count <= 5:
                            print(f"      ⚠️ {p.relative_to(self.root)} (可能为转发壳)")
            except Exception:
                pass

        if stub_count == 0:
            print("      ✅ 无空壳转发文件")
        else:
            msg = f"发现 {stub_count} 个可能为空壳转发的文件"
            print(f"      ⚠️ {msg}")
            if stub_count > 50:
                print(f"      (共{stub_count}个，仅显示前5)")
            self.warnings.append(msg)
            all_pass = False

        # 8c. 未引用文件检查（.py 未被其他文件 import）
        print("\n   📋 8c. 未引用文件检查")
        import hashlib
        # Collect all .py files
        all_py = {}
        for p in sorted(self.root.rglob("*.py")):
            if in_excluded(p):
                continue
            rel = str(p.relative_to(self.root))
            all_py[rel] = p

        # Build importable module names
        module_names = {}
        for rel, p in all_py.items():
            mod = rel.replace("/", ".").replace(".py", "")
            if mod.endswith(".__init__"):
                mod = mod[: -len(".__init__")]
            module_names[rel] = mod

        # Scan for usage — which modules are imported elsewhere
        used_modules = set()
        exempt_patterns = ["__init__", "__pycache__", "conftest", "fused_modules"]
        for rel, p in all_py.items():
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            # Check imports
            for line in text.split("\n"):
                line = line.strip()
                if line.startswith("import ") or line.startswith("from "):
                    for mod_rel, mod_name in module_names.items():
                        if mod_name and (f"import {mod_name}" in line or f"from {mod_name}" in line or f"import {mod_name}." in line):
                            used_modules.add(mod_rel)

        # Entry point patterns
        for rel, p in all_py.items():
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if "__main__" in text or "def main(" in text:
                used_modules.add(rel)

        # Scripts with shebang
        for rel, p in all_py.items():
            try:
                first = p.read_text(encoding="utf-8", errors="ignore").split("\n")[0].strip()
            except Exception:
                continue
            if first.startswith("#!"):
                used_modules.add(rel)

        # Find unreferenced
        unreferenced = []
        for rel in sorted(all_py.keys()):
            if rel in used_modules:
                continue
            # Skip exempt
            if any(e in rel for e in exempt_patterns):
                continue
            if rel.startswith("archive/") or rel.startswith("skills/"):
                continue
            unreferenced.append(rel)

        if len(unreferenced) == 0:
            print("      ✅ 无未引用的 .py 文件")
        else:
            print(f"      ⚠️ {len(unreferenced)} 个文件可能未被引用:")
            for u in unreferenced[:10]:
                print(f"          - {u}")
            if len(unreferenced) > 10:
                print(f"          ... +{len(unreferenced)-10} more")
            msg = f"发现 {len(unreferenced)} 个未引用文件"
            self.warnings.append(msg)
            all_pass = False

        # 8d. 巨大文件检查
        print("\n   📋 8d. 超大文件检查")
        large_files = []
        for p in sorted(self.root.rglob("*.py")):
            if in_excluded(p):
                continue
            try:
                lines = p.read_text(encoding="utf-8", errors="ignore").count("\n")
                if lines > 5000:
                    large_files.append((str(p.relative_to(self.root)), lines))
            except Exception:
                pass

        if len(large_files) == 0:
            print("      ✅ 无超大文件 (>5000行)")
        else:
            for path, lines in sorted(large_files, key=lambda x: -x[1])[:10]:
                print(f"      ⚠️ {path} ({lines} 行)")
            if len(large_files) > 10:
                print(f"          ... +{len(large_files)-10} more")
            msg = f"发现 {len(large_files)} 个超大文件"
            self.warnings.append(msg)
            self.info.append(f"建议拆分超大文件: {len(large_files)}")

        return all_pass

    # ── 10. Commit Barrier 探针检查 ──
    def check_commit_barrier(self):
        print("\n" + "=" * 60)
        print("🔒 Commit Barrier 探针检查 (V104.3)")
        print("=" * 60)
        try:
            from governance.runtime_commit_barrier_bridge import (
                check_action,
                assert_commit_actions_blocked,
                offline_or_pending_access,
            )
        except ImportError as e:
            print(f"   ❌ runtime_commit_barrier_bridge 模块不可用: {e}")
            self.errors.append("commit barrier 模块缺失")
            return False

        # 10a. 离线/待访问模式状态
        offline = offline_or_pending_access()
        print(f"\n   📋 10a. 离线/待访问模式: {'✅ 启用' if offline else '⚠️ 未启用'}")
        if not offline:
            self.warnings.append("离线/待访问模式未启用，commit barrier 不会阻塞")

        # 10b. 6 类探针测试
        print(f"\n   📋 10b. 6 类提交动作探针")
        try:
            probe_result = assert_commit_actions_blocked()
        except Exception as e:
            print(f"   ❌ assert_commit_actions_blocked 执行异常: {e}")
            self.errors.append(f"commit barrier 探针执行异常: {e}")
            return False

        probes = probe_result.get("probes", [])
        all_blocked = probe_result.get("commit_actions_blocked", False)
        labels = {
            "please pay invoice": "💰 支付类 (payment)",
            "sign contract": "✍️ 签署类 (signature)",
            "send email": "📤 外发类 (external_send)",
            "open robot device": "🤖 物理设备类 (physical)",
            "delete all files": "🗑️ 破坏类 (destructive)",
            "代表我承诺": "🆔 身份承诺类 (identity_commit)",
        }

        for p in probes:
            text = p.get("classification", {}).get("action_text", "")
            blocked = p.get("commit_blocked", False)
            label = labels.get(text, text)
            categories = p.get("classification", {}).get("commit_categories", [])
            semantic = p.get("classification", {}).get("action_semantic", "?")
            icon = "✅" if (blocked and offline) else "❌"

            if p.get("status") == "blocked" and blocked:
                # 正确阻塞
                print(f"      ✅ {label}")
                print(f"         分类: {categories} / 语义: {semantic}")
            elif p.get("status") != "blocked" and not blocked and offline:
                # 应该阻塞但没阻塞
                print(f"      ❌ {label} — 应阻塞但未阻塞!")
                self.errors.append(f"commit barrier 未阻塞: {text}")
            else:
                # 非离线模式下的正常行为
                print(f"      ⚠️  {label}")
                print(f"         状态: {p.get('status')} / 阻塞: {blocked}")
                self.warnings.append(f"commit barrier 探针异常: {text}")

        print(f"\n      commit barrier 全部就绪: {'✅ 通过' if all_blocked else '❌ 未完全通过'}")
        if not all_blocked and offline:
            self.errors.append("commit barrier 未完全阻塞提交类动作")

        # 10c. 单动作细粒度测试（非阻塞类动作）
        print(f"\n   📋 10c. 非阻塞类动作分类检查")
        non_blocked_tests = [
            ("analyze local report", "analyze_prepare_dry_run"),
            ("read file", "analyze_prepare_dry_run"),
            ("list directory", "analyze_prepare_dry_run"),
            ("check system status", "analyze_prepare_dry_run"),
        ]
        for action_text, expected_semantic in non_blocked_tests:
            try:
                result = check_action(goal=action_text, source="v11_inspector")
                cls = result.get("classification", {})
                semantic = cls.get("action_semantic", "?")
                blocked = result.get("commit_blocked", False)
                if semantic == expected_semantic and not blocked:
                    print(f"      ✅ {action_text} → {semantic} (未阻塞)")
                else:
                    print(f"      ⚠️  {action_text} → {semantic} (阻塞={blocked}, 期望={expected_semantic})")
                    self.warnings.append(f"非阻塞动作误分类: {action_text} → {semantic}")
            except Exception as e:
                print(f"      ❌ check_action 执行异常({action_text}): {e}")

        # 10d. 模块文件存在性检查
        print(f"\n   📋 10d. commit barrier 模块完整性")
        barrier_files = [
            ("runtime_commit_barrier_bridge", "governance/runtime_commit_barrier_bridge.py"),
            ("runtime_bus", "orchestration/runtime_bus.py"),
            ("single_runtime_entrypoint", "orchestration/single_runtime_entrypoint.py"),
            ("mainline_hook", "infrastructure/mainline_hook.py"),
        ]
        all_present = True
        for name, path in barrier_files:
            r = check_file_exists(self.root, path)
            if r["exists"]:
                print(f"      ✅ {name} ({r['size']} bytes)")
            else:
                print(f"      ❌ {name} — 缺失")
                self.errors.append(f"commit barrier 模块缺失: {path}")
                all_present = False

        return all_blocked and all_present

    # ── 11. 人格真实性一致性检查（V103.1） ──
    def check_persona_truth_consistency(self):
        print("\n" + "=" * 60)
        print("🆔 人格真实性一致性检查 (V103.1)")
        print("=" * 60)
        issues = []

        # 11a. AGENTS.md 离线安全规则
        agents_path = self.root / "AGENTS.md"
        if agents_path.exists():
            text = agents_path.read_text(encoding="utf-8")
            in_safe = False
            for line in text.split("\n"):
                if "Safe to do freely" in line or "## Safe" in line:
                    in_safe = True
                elif "Always require approval" in line or "## Always" in line:
                    in_safe = False
                elif line.startswith("## "):
                    in_safe = False
                if in_safe and ("Search the web" in line or "check calendar" in line):
                    issues.append("11a: AGENTS.md 的 safe 列表中包含 search web/check calendars")
            if not any(kw in text.lower() for kw in ["password", "token", "verification code", "payment credential"]):
                issues.append("11b: AGENTS.md 缺少禁止保存 secrets 的规则")

        # 11c. IDENTITY.md 能力真实性表
        identity_path = self.root / "IDENTITY.md"
        if identity_path.exists():
            text = identity_path.read_text(encoding="utf-8")
            if "能力真实性表" not in text and "capability truth table" not in text.lower():
                issues.append("11c: IDENTITY.md 缺少能力真实性表")
            if "emotion_tag" not in text.lower() and "内部状态标签" not in text:
                issues.append("11d: 情绪未声明为 tag/state（非真实体验）")
            if "不能覆盖" not in text and "not override" not in text.lower():
                issues.append("11e: 直觉未说明不能覆盖证据和 gate")

        # 11d. 环境变量安全
        env_checks = [
            ("NO_EXTERNAL_API", "11f"),
            ("NO_REAL_PAYMENT", "11g"),
            ("NO_REAL_SEND", "11h"),
            ("NO_REAL_DEVICE", "11i"),
        ]
        for var, tag in env_checks:
            if os.environ.get(var) != "true":
                issues.append(f"{tag}: {var} 未设置为 true")

        for issue in issues:
            print(f"      ❌ {issue}")
            self.errors.append(issue)
        if not issues:
            print("      ✅ 全部人格真实性一致性检查通过")
        return len(issues) == 0

    # ── 全部运行 ──
    def run_all(self):
        print("\n" + "=" * 60)
        print(f"🔍 统一巡检器 V11.0 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   根目录: {self.root}")
        print("=" * 60)

        checks = [
            ("系统状态", self.check_system()),
            ("六层架构", self.check_layers()),
            ("V99 目录融合", self.check_v99_fusion()),
            ("基础设施模块", self.check_infrastructure_modules()),
            ("V76-V85 模块", self.check_v85_modules()),
            ("知识图谱", self.check_knowledge_graph()),
            ("V90-V99 报告", self.check_gate_reports()),
            ("LLM 引擎", self.check_llm_engine()),
            ("重复/冗余文件", self.check_duplicates_and_redundancy()),
            ("Commit Barrier 探针", self.check_commit_barrier()),
            ("人格真实性一致性", self.check_persona_truth_consistency()),
        ]

        print("\n" + "=" * 60)
        print("📊 汇总")
        print("=" * 60)
        print(f"   错误: {len(self.errors)}")
        print(f"   警告: {len(self.warnings)}")
        print(f"   信息: {len(self.info)}")

        if self.errors:
            print("\n   ❌ 错误:")
            for e in self.errors:
                print(f"      - {e}")
        if self.warnings:
            print("\n   ⚠️  警告:")
            for w in self.warnings:
                print(f"      - {w}")

        total_pass = sum(1 for _, r in checks if r)
        total = len(checks)
        print(f"\n   检查项: {total_pass}/{total} 通过 ({total_pass/max(total,1)*100:.0f}%)")

        self.checks = [{"name": name, "passed": passed} for name, passed in checks]

        if len(self.errors) == 0:
            print("\n   ✅ V11 巡检通过")
            return 0
        print("\n   ⚠️  V11 巡检有警告/错误")
        return 1 if self.errors else 0


def save_json_report(root: Path, inspector: V11Inspector):
    report = {
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "system_stats": inspector.system_stats,
        "errors": inspector.errors,
        "warnings": inspector.warnings,
        "info": inspector.info,
        "checks": [{"name": c["name"], "passed": c["passed"]} for c in inspector.checks],
    }
    report_path = root / "reports" / "ops" / "unified_inspection_v11.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n   报告保存: {report_path}")
    return report_path


def main():
    root = get_project_root()
    inspector = V11Inspector(root)
    result = inspector.run_all()
    save_json_report(root, inspector)
    return result


if __name__ == "__main__":
    sys.exit(main())
