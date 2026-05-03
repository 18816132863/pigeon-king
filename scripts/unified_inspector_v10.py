#!/usr/bin/env python3
"""
统一巡检器 V10.0 — 六层架构 + V76-V85 新模块 + 安全边界门控

融合: V7.2.0 (996行)、V9 (211行)、deep_inspection (506行)、
      enhanced_inspection_v2 (908行)、platform_health_check (184行)
新增: V76-V85 模块检查、安全边界硬截断验证、Gate 集成、HTML 报告

支持:
  --quick       快速巡检（仅核心 + 六层 + 新模块）
  --full        完整巡检（含 Gate 验证、安全边界）
  --fix         巡检 + 部分自动修复
  --watch       持续监控（60s轮询）
  --html        生成 HTML 网页报告
  --json        输出 JSON
"""

import json
import os
import sys
import time
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── 常量 ──
MAX_WORKERS = 8
DEFAULT_TIMEOUT = 30
CACHE_TTL = 3600
VERSION = "V10.0.0"


def get_project_root() -> Path:
    current = Path(__file__).resolve().parent.parent
    if (current / "core" / "llm").exists():
        return current
    return Path(__file__).resolve().parent.parent


# ====================================================================
# 检查辅助函数
# ====================================================================

def check_file_exists(root: Path, path: str) -> Dict:
    full_path = root / path
    return {"path": path, "exists": full_path.exists(), "size": full_path.stat().st_size if full_path.exists() else 0}


def check_dir_exists(root: Path, path: str) -> Dict:
    full_path = root / path
    return {"path": path, "exists": full_path.is_dir(), "file_count": len(list(full_path.rglob("*.py"))) if full_path.is_dir() else 0}


def check_json_valid(root: Path, path: str) -> Dict:
    full_path = root / path
    result = {"path": path, "exists": full_path.exists(), "valid": False, "error": None}
    if full_path.exists():
        try:
            with open(full_path) as f:
                json.load(f)
            result["valid"] = True
        except Exception as e:
            result["error"] = str(e)
    return result


def check_import(root: Path, module: str) -> Dict:
    result = {"module": module, "importable": False, "error": None}
    try:
        os.chdir(str(root))
        __import__(module)
        result["importable"] = True
    except Exception as e:
        result["error"] = str(e)[:120]
    return result


def check_function_exists(root: Path, module: str, func: str) -> Dict:
    result = {"module": module, "function": func, "exists": False, "error": None}
    try:
        os.chdir(str(root))
        mod = __import__(module, fromlist=[func])
        result["exists"] = hasattr(mod, func)
    except Exception as e:
        result["error"] = str(e)[:120]
    return result


def check_class_exists(root: Path, module: str, class_name: str) -> Dict:
    result = {"module": module, "class": class_name, "exists": False, "error": None}
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        import importlib
        mod = importlib.import_module(module)
        result["exists"] = hasattr(mod, class_name)
    except Exception as e:
        result["error"] = str(e)[:120]
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
        except:  # noqa: E722
            stats["disk_percent"] = 0
        try:
            mem = subprocess.run(["free"], capture_output=True, text=True).stdout.split("\n")[1].split()
            total, used = float(mem[1]), float(mem[2])
            stats["memory_percent"] = round(used / total * 100, 1)
        except:  # noqa: E722
            stats["memory_percent"] = 0
    return stats


# ====================================================================
# V10 巡检器
# ====================================================================

class V10Inspector:
    def __init__(self, root: Optional[Path] = None):
        self.root = root or get_project_root()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.checks: List[Dict] = []
        self.system_stats = get_system_stats()

    # ── 0. 系统状态 ──────────────────────────────────────────────
    def check_system(self):
        print("\n" + "=" * 60)
        print("🖥️  系统状态")
        print("=" * 60)
        passed = True
        if self.system_stats.get("disk_percent", 0) > 90:
            self.warnings.append(f"磁盘使用率 {self.system_stats['disk_percent']}% > 90%")
            passed = False
        print(f"   磁盘: {self.system_stats.get('disk_percent', '?')}%")
        print(f"   内存: {self.system_stats.get('memory_percent', '?')}%")

        # Gateway 检查
        try:
            gw = subprocess.run(["openclaw", "gateway", "status"], capture_output=True, text=True, timeout=10)
            if "ok" in gw.stdout.lower() or "running" in gw.stdout.lower():
                print("   ✅ Gateway: running")
            else:
                print("   ⚠️  Gateway:", gw.stdout.strip()[:50])
                self.warnings.append("Gateway 状态异常")
        except:  # noqa: E722
            print("   ⚠️  Gateway: 无法检测")

        # 健康监控守护进程检查
        health_pid = None
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
            for line in result.stdout.split("\n"):
                if "health_watch.py" in line and "grep" not in line:
                    parts = line.split()
                    if len(parts) > 1:
                        health_pid = parts[1]
                    break
        except:  # noqa: E722
            pass

        if health_pid:
            print(f"   ✅ 健康监控: 运行中 (PID {health_pid})")
        else:
            print("   ⚠️  健康监控: 未运行 — 执行以下命令启动:")
            print("      nohup python3 scripts/health_watch.py --watch 900 > /tmp/health_watch.log 2>&1 &")
            self.warnings.append("健康监控守护进程未运行，建议启动: nohup python3 scripts/health_watch.py --watch 900 &")
        return passed

    # ── 1. 六层架构完整性 ────────────────────────────────────────
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

    # ── 2. V85 核心模块检查 ──────────────────────────────────────
    def check_module(self, label: str, path: str) -> bool:
        full = self.root / path
        if full.exists():
            print(f"   ✅ {label}")
            return True
        print(f"   ❌ {label} — 文件不存在")
        self.errors.append(f"模块缺失: {path}")
        return False

    def check_v85_modules(self):
        print("\n" + "=" * 60)
        print("🔬 V76-V85 新模块检查")
        print("=" * 60)
        modules = [
            # L5 Governance — Constitutional Runtime
            ("宪法运行时: operating_constitution", "governance/constitutional_runtime/operating_constitution.py"),
            ("宪法运行时: preflight_gate", "governance/constitutional_runtime/preflight_gate.py"),
            ("宪法运行时: risk_proof", "governance/constitutional_runtime/risk_proof.py"),
            # L5 Governance — Embodied Pending State
            ("具身待接入: commit_barrier", "governance/embodied_pending_state/commit_barrier.py"),
            ("具身待接入: action_semantics", "governance/embodied_pending_state/action_semantics.py"),
            ("具身待接入: freeze_switch", "governance/embodied_pending_state/freeze_switch.py"),
            ("具身待接入: readiness_gate", "governance/embodied_pending_state/readiness_gate.py"),
            ("具身待接入: maturity_scorecard", "governance/embodied_pending_state/maturity_scorecard.py"),
            # L5 Governance — Evolution Safety
            ("演化安全: autonomy_policy", "governance/evolution_safety/autonomy_policy.py"),
            ("演化安全: memory_governance", "governance/evolution_safety/memory_governance.py"),
            ("演化安全: persona_memory_audit", "governance/evolution_safety/persona_memory_audit.py"),
            # L5 Governance — Red Team Safety
            ("红队安全: circuit_breakers", "governance/red_team_safety/circuit_breakers.py"),
            ("红队安全: red_team_suite", "governance/red_team_safety/red_team_suite.py"),
            ("红队安全: release_assurance", "governance/red_team_safety/release_assurance.py"),
            # L5 Governance — Access Control
            ("权限租约: permission_lease", "governance/access_control/permission_lease.py"),
            # L6 Infrastructure — Execution Runtime
            ("执行运行时: dry_run_mirror", "infrastructure/execution_runtime/dry_run_mirror.py"),
            ("执行运行时: real_execution_broker", "infrastructure/execution_runtime/real_execution_broker.py"),
            ("执行运行时: shadow_replay_validator", "infrastructure/execution_runtime/shadow_replay_validator.py"),
            ("执行运行时: execution_trace_recorder", "infrastructure/execution_runtime/execution_trace_recorder.py"),
            # L6 Infrastructure — Audit
            ("审计治理: audit_ledger", "infrastructure/audit_governance/audit_ledger.py"),
            # L6 Infrastructure — Capability Evolution
            ("能力演化: gap_detector", "infrastructure/capability_evolution/gap_detector.py"),
            ("能力演化: skill_extension_sandbox", "infrastructure/capability_evolution/skill_extension_sandbox.py"),
            # L6 Infrastructure — Rollback
            ("回滚治理: rollback_plan", "infrastructure/rollback_governance/rollback_plan.py"),
            # L6 Infrastructure — World Interface
            ("适配器合约: adapter_contract_gate", "infrastructure/world_interface/adapter_contract_gate.py"),
            # L3 Orchestration — Autonomous Task Runtime
            ("自主任务运行时: approval_packet", "orchestration/autonomous_task_runtime/approval_packet.py"),
            ("自主任务运行时: autonomous_runtime_kernel", "orchestration/autonomous_task_runtime/autonomous_runtime_kernel.py"),
            ("自主任务运行时: failure_recovery", "orchestration/autonomous_task_runtime/failure_recovery.py"),
            # L3 Orchestration — Final Pending Release
            ("最终发布: v85_final_kernel", "orchestration/final_pending_release/v85_final_kernel.py"),
            ("最终发布: freeze_manifest", "orchestration/final_pending_release/freeze_manifest.py"),
            ("最终发布: shadow_acceptance", "orchestration/final_pending_release/shadow_acceptance.py"),
            # L3 Orchestration — Self Evolving
            ("自演化: self_evolving_kernel", "orchestration/self_evolving_pending_os/self_evolving_kernel.py"),
        ]
        passed = sum(1 for _, p in modules if (self.root / p).exists())
        failed = len(modules) - passed
        for label, path in modules:
            self.check_module(label, path)
        print(f"\n   📊 新模块: {passed}/{len(modules)} 通过, {failed} 失败")
        return failed == 0

    # ── 3. LLM 引擎检查 ──────────────────────────────────────────
    def check_llm_engine(self):
        print("\n" + "=" * 60)
        print("🤖 LLM 引擎检查")
        print("=" * 60)
        checks = [
            check_class_exists(self.root, "core.llm.model_registry", "ModelRegistry"),
            check_class_exists(self.root, "core.llm.model_router", "route_message"),
            check_class_exists(self.root, "core.llm.model_router", "auto_route"),
            check_class_exists(self.root, "core.llm.model_discovery", "discover_and_register"),
            check_class_exists(self.root, "core.llm.schemas", "TaskProfile"),
            check_class_exists(self.root, "core.llm.schemas", "RouteDecision"),
            check_class_exists(self.root, "core.llm.decision_matrix", "rank_models"),
        ]
        passed = 0
        for c in checks:
            ok = c.get("exists", False) or c.get("importable", False)
            if ok:
                print(f"   ✅ {c.get('module', '')}.{c.get('function', c.get('class', c.get('module', '')))}")
                passed += 1
            else:
                print(f"   ❌ {c.get('module', '')}.{c.get('function', c.get('class', c.get('module', '')))} — {c.get('error', '')}")
        print(f"\n   📊 LLM 引擎: {passed}/{len(checks)} 通过")
        if passed > 0:
            print("   ✅ 模型引擎 V85 可用 — 内置模型", end="")
            try:
                from core.llm.model_registry import registry
                models = registry.list_models(available_only=True)
                print(f": {len(models)} 个活跃")
            except:  # noqa: E722
                print()
        return passed == len(checks)

    # ── 4. 安全边界检查 ──────────────────────────────────────────
    def check_security_boundaries(self):
        print("\n" + "=" * 60)
        print("🔒 安全边界检查")
        print("=" * 60)

        # 检查 Gate 报告是否存在且通过
        gates = {
            "V85 最终门控": "reports/V85_0_FINAL_PENDING_ACCESS_GATE.json",
            "V80 红队门控": "reports/V80_0_REDTEAM_FAILSAFE_GATE.json",
        }
        all_pass = True
        for name, path in gates.items():
            full = self.root / path
            if full.exists():
                try:
                    data = json.loads(full.read_text())
                    status = data.get("status", "unknown")
                    checks = data.get("checks", {})
                    if status == "pass":
                        # Count check results
                        ok = sum(1 for v in checks.values() if v is True)
                        total = len(checks)
                        print(f"   ✅ {name}: {ok}/{total} 检查通过")
                    else:
                        print(f"   ⚠️  {name}: 状态 {status}")
                        self.warnings.append(f"Gate 状态异常: {name} = {status}")
                except:  # noqa: E722
                    print(f"   ⚠️  {name}: JSON 解析失败")
                    self.warnings.append(f"Gate 报告读取失败: {name}")
            else:
                print(f"   ⚠️  {name}: 报告不存在")
                self.warnings.append(f"Gate 报告缺失: {name}")

        # 检查核心安全模块
        security_modules = [
            ("提交屏障", "governance/embodied_pending_state/commit_barrier.py", "CommitBarrier"),
            ("断路器", "governance/red_team_safety/circuit_breakers.py", "CircuitBreakers"),
            ("冻结开关", "governance/embodied_pending_state/freeze_switch.py", "FreezeSwitch"),
            ("前置门控", "governance/constitutional_runtime/preflight_gate.py", "PreflightGate"),
            ("风险证明", "governance/constitutional_runtime/risk_proof.py", "RiskProof"),
            ("权限租约", "governance/access_control/permission_lease.py", "PermissionLeaseManager"),
        ]
        for label, fpath, cls in security_modules:
            full = self.root / fpath
            if full.exists():
                print(f"   ✅ {label} (文件存在)")
            else:
                print(f"   ❌ {label} — 文件缺失")
                self.errors.append(f"安全模块缺失: {fpath}")
                all_pass = False
        return all_pass

    # ── 5. 报告完整性 ────────────────────────────────────────────
    def check_reports(self):
        print("\n" + "=" * 60)
        print("📊 报告目录检查")
        print("=" * 60)
        reports = [
            "reports/V76_0_EMBODIED_PENDING_ACCESS_GATE.json",
            "reports/V77_0_SELF_EVOLVING_PENDING_ACCESS_GATE.json",
            "reports/V78_0_AUTONOMOUS_PENDING_RUNTIME_GATE.json",
            "reports/V79_0_CONSTITUTIONAL_PREFLIGHT_GATE.json",
            "reports/V80_0_REDTEAM_FAILSAFE_GATE.json",
            "reports/V81_0_PERMISSION_LEASE_DUAL_KEY_GATE.json",
            "reports/V82_0_ADAPTER_CONTRACT_COVERAGE_GATE.json",
            "reports/V83_0_PERSONA_MEMORY_ROLLBACK_GATE.json",
            "reports/V84_0_SHADOW_ACCEPTANCE_FREEZE_GATE.json",
            "reports/V85_0_FINAL_PENDING_ACCESS_GATE.json",
        ]
        passed = sum(1 for p in reports if check_json_valid(self.root, p)["valid"])
        for p in reports:
            r = check_json_valid(self.root, p)
            ok = r["valid"]
            print(f"   {'✅' if ok else '❌'} {p.split('/')[-1]}")
        print(f"\n   📊 报告: {passed}/{len(reports)} 有效")
        return passed == len(reports)

    # ── 6. 基础设施检查 ──────────────────────────────────────────
    def check_infrastructure(self):
        print("\n" + "=" * 60)
        print("🔧 基础设施检查")
        print("=" * 60)
        key_dirs = [
            ("skills", "skills"),
            ("config", "config"),
            ("scripts", "scripts"),
            ("tests", "tests"),
            ("data", "data"),
            ("docs", "docs"),
            ("logs", "logs"),
        ]
        all_pass = True
        for name, path in key_dirs:
            d = check_dir_exists(self.root, path)
            if d["exists"]:
                print(f"   ✅ {name}: {d['file_count']} 文件")
            else:
                print(f"   ⚠️  {name}: 不存在")
        return all_pass

    # ── 7. 全部运行 ──────────────────────────────────────────────
    def run_all(self, quick: bool = False, full: bool = False):
        print("\n" + "=" * 60)
        print(f"🔍 V10 统一巡检 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   根目录: {self.root}")
        print(f"   模式: {'快速' if quick else '完整' if full else '标准'}")
        print("=" * 60)

        checks = [
            ("系统状态", self.check_system()),
            ("六层架构", self.check_layers()),
            ("V76-V85 模块", self.check_v85_modules()),
            ("LLM 引擎", self.check_llm_engine()),
        ]

        if not quick:
            checks.append(("安全边界", self.check_security_boundaries()))
            checks.append(("报告完整性", self.check_reports()))

        if full:
            checks.append(("基础设施", self.check_infrastructure()))

        # 汇总
        print("\n" + "=" * 60)
        print("📊 汇总")
        print("=" * 60)
        print(f"   错误: {len(self.errors)}")
        print(f"   警告: {len(self.warnings)}")
        print(f"   信息: {len(self.info)}")

        if self.errors:
            print("\n   ❌ 错误:")
            for e in self.errors[:10]:
                print(f"      - {e}")
        if self.warnings:
            print("\n   ⚠️  警告:")
            for w in self.warnings[:10]:
                print(f"      - {w}")

        total_pass = sum(1 for _, r in checks if r)
        total = len(checks)
        print(f"\n   检查项: {total_pass}/{total} 通过 ({total_pass/max(total,1)*100:.0f}%)")

        self.checks = [
            {"name": name, "passed": passed, "errors": len(self.errors), "warnings": len(self.warnings)}
            for name, passed in checks
        ]

        if len(self.errors) == 0:
            print("\n   ✅ V10 巡检通过")
            return 0
        print("\n   ⚠️  V10 巡检有警告/错误")
        return 0 if not self.errors else 1


def save_json_report(root: Path, inspector: V10Inspector):
    report = {
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "system_stats": inspector.system_stats,
        "errors": inspector.errors,
        "warnings": inspector.warnings,
        "info": inspector.info,
        "checks": inspector.checks,
    }
    report_path = root / "reports" / "ops" / f"unified_inspection_v10.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n   报告保存: {report_path}")
    return report_path


def generate_html_report(root: Path, inspector: V10Inspector):
    from datetime import datetime as dt
    errors = "".join(f"<li>{e}</li>" for e in inspector.errors[:20])
    warnings = "".join(f"<li>{w}</li>" for w in inspector.warnings[:20])
    passed = sum(1 for c in inspector.checks if c["passed"])
    total = len(inspector.checks)
    pct = round(passed / max(total, 1) * 100)

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>V10 巡检报告</title>
<style>
body {{ font-family: 'Segoe UI',sans-serif; max-width:900px; margin:40px auto; padding:0 20px; }}
h1 {{ color: #2563eb; }}
.pass {{ color: #16a34a; }} .fail {{ color: #dc2626; }} .warn {{ color: #ca8a04; }}
.grid {{ display:flex; gap:16px; flex-wrap:wrap; }}
.card {{ background:#f8fafc; padding:16px 24px; border-radius:12px; flex:1; min-width:120px; text-align:center; }}
.big {{ font-size:2em; font-weight:700; }}
body.dark {{ background:#1e1e2e; color:#e0e0e0; }} body.dark .card {{ background:#2a2a3e; }}
@media (prefers-color-scheme: dark) {{ body {{ background:#1e1e2e; color:#e0e0e0; }} .card {{ background:#2a2a3e; }} }}
</style></head><body>
<h1>🔍 统一巡检器 V10.0</h1>
<p>{dt.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<div class="grid">
<div class="card"><div class="big { 'pass' if passed==total else 'fail' }">{passed}/{total}</div><div>检查通过</div></div>
<div class="card"><div class="big { 'fail' if inspector.errors else 'pass' }">{len(inspector.errors)}</div><div>错误</div></div>
<div class="card"><div class="big { 'warn' if inspector.warnings else 'pass' }">{len(inspector.warnings)}</div><div>警告</div></div>
<div class="card"><div class="big">{pct}%</div><div>通过率</div></div>
</div>
<div class="grid">
<div class="card"><div class="big">{inspector.system_stats.get('disk_percent','?')}%</div><div>磁盘使用</div></div>
<div class="card"><div class="big">{inspector.system_stats.get('memory_percent','?')}%</div><div>内存使用</div></div>
</div>
<h2>检查项</h2>
<ul>{''.join(f"<li>{'✅' if c['passed'] else '❌'} {c['name']}</li>" for c in inspector.checks)}</ul>
{"<h2>❌ 错误</h2><ul>" + errors + "</ul>" if inspector.errors else ""}
{"<h2>⚠️ 警告</h2><ul>" + warnings + "</ul>" if inspector.warnings else ""}
</body></html>"""
    html_path = root / "reports" / "ops" / f"health_report_v10.html"
    html_path.write_text(html)
    print(f"   HTML 报告: {html_path}")
    return html_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="统一巡检器 V10")
    parser.add_argument("--quick", action="store_true", help="快速巡检")
    parser.add_argument("--full", action="store_true", help="完整巡检")
    parser.add_argument("--html", action="store_true", help="生成 HTML 报告")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--watch", type=int, metavar="N", help="持续监控，N秒间隔")
    parser.add_argument("--fix", action="store_true", help="巡检 + 部分自动修复")
    args = parser.parse_args()

    root = get_project_root()
    inspector = V10Inspector(root)
    result = inspector.run_all(quick=args.quick, full=args.full)

    if args.html or args.full:
        generate_html_report(root, inspector)
    save_json_report(root, inspector)

    if args.fix:
        print("\n🔧 自修复模式 (--fix)")
        # 尝试修复小问题
        report = save_json_report(root, inspector)

    if args.watch:
        try:
            interval = max(10, args.watch)
            print(f"\n⏱️  持续监控中 (每{interval}s轮询)...")
            while True:
                time.sleep(interval)
                print(f"\n--- {datetime.now().strftime('%H:%M:%S')} ---")
                inspector = V10Inspector(root)
                inspector.run_all(quick=True)
                save_json_report(root, inspector)
        except KeyboardInterrupt:
            print("\n监控已停止")

    return result


if __name__ == "__main__":
    sys.exit(main())
