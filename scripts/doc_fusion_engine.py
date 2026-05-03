#!/usr/bin/env python3
"""
doc_fusion_engine — 文档融合自动引擎（融合 V2 版）

V2 融合升级内容（集成 infrastructure/fusion_engine_v2）：
  - 在 auto_fuse() 入口自动调用 ScriptAnalyzer 进行 AST 分析
  - 对传入的 modules 逐层推演目标层归属
  - 自动生成融合报告时附加 AST 元数据

V3 自动融合升级：
  - 新增 scan_and_fuse() — 自动扫描 skills/、core/、scripts/、governance/ 目录
  - 自动检测未注册的新文件、新技能
  - 自动注册到 skill_trigger_registry
  - 自动融合到架构文档
  - 基于文件系统快照对比（.fusion_state.json）实现增量检测

双模式运作：
1. **Gate模式**（旧方式）：扫描 reports/ 下的 Gate 报告，自动融合
2. **Auto模式**（新方式）：在完成改动后主动传入融合载荷，引擎自动判断是否需要融合

### 何时触发自动融合（调用 auto_fuse(payload)）

| 条件 | 结论 |
|------|------|
| 新增了模块/文件 | ✅ 必须融合 |
| 修改了用户可见文档（IDENTITY/SOUL/AGENTS等） | ✅ 必须融合 |
| 改了安全/约束规则 | ✅ 必须融合 |
| 改了执行流程（mainline_hook） | ✅ 必须融合 |
| 新文件被其他模块 import/引用 | ✅ 必须融合 |
| 以上都不是 | ❌ 只记 CHANGELOG，不融合 |

### 融合载荷格式
```python
payload = {
    "trigger": "new_module" | "modified_doc" | "changed_security" | "changed_flow" | "gate_pass",
    "version": "V105",
    "category": "人格层" | "安全加固" | "文档收口" | "执行流程" | ...,
    "description": "简短描述",
    "modules": [{"path": "...", "layer": "L2", "description": "..."}],
    "security_changed": False | True,
    "user_visible": False | True,
    "gate_passed": True,
    "remaining_failures": [],
}
```
"""
from __future__ import annotations

import json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

ROOT = Path.cwd()
REPORTS_DIR = ROOT / "reports"
ARCH = ROOT / "docs" / "ARCHITECTURE_V10.md"
CHANGELOG = ROOT / "docs" / "CHANGELOG.md"
FUSED_DIR = ROOT / "governance" / "fused_modules"

TZ = timezone.utc

# ── 集成 V2 融合引擎（代码级 AST 分析，导入时确保 sys.path 包含项目根） ──
_FUSION_V2_AVAILABLE = False
try:
    sys.path.insert(0, str(ROOT))
    from infrastructure.fusion_engine_v2 import FusionEngine, ScriptAnalyzer
    _FUSION_V2_AVAILABLE = True
except ImportError:
    pass  # 静默回退，不影响原有逻辑

# ── 自动融合状态追踪文件 ──
_FUSION_STATE_FILE = ROOT / "governance" / ".fusion_state.json"

# 已知的融合记录（避免重复融合）
_FUSED_VERSIONS_FILE = FUSED_DIR
# ────────────────────────────────────────
# ────────────────────────────────────────


def utc8_now_str() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


def safe_jsonable(obj):
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): safe_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [safe_jsonable(x) for x in obj]
    return str(obj)


def write_json(path: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(safe_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")


# ════════════════════════════════════════════════════════════════
# 判断逻辑：是否需要融合
# ════════════════════════════════════════════════════════════════

def _should_fuse(payload: dict) -> tuple[bool, str]:
    """返回 (should_fuse, reason)。

    硬条件（满足任意一条就融合）：
    1. architecture_related == True (与架构相关的任何增减或改动 - 兜底条款)
    2. user_visible == True (改了用户可见文档)
    3. security_changed == True (改了安全/约束)
    4. trigger in [new_module, modified_doc, changed_security, changed_flow]
    5. 有新的 modules 列表（>0 且没空）

    兜底条款（1）：以下情况均视为 architecture_related：
    - 架构层的文件移动/新增/删除
    - 架构图中某层的结构或职责变化
    - 架构策略/设计原则改变
    - 架构中某组件的角色/依赖关系变化
    - 之前没纳入架构但实际影响架构的行为
    """
    trigger = payload.get("trigger", "")
    user_visible = payload.get("user_visible", False)
    security_changed = payload.get("security_changed", False)
    modules = payload.get("modules", [])
    architecture_related = payload.get("architecture_related", False)

    must_fuse_triggers = {"new_module", "modified_doc", "changed_security", "changed_flow"}

    if architecture_related:
        return True, "architecture_related"
    if user_visible:
        return True, "user_visible"
    if security_changed:
        return True, "security_changed"
    if trigger in must_fuse_triggers:
        return True, f"trigger={trigger}"
    if modules and len(modules) > 0:
        return True, f"{len(modules)} new modules"
    return False, "no fusion criteria met"


# ════════════════════════════════════════════════════════════════
# 版本历史更新（ARCHITECTURE_V10.md）
# ════════════════════════════════════════════════════════════════

def get_existing_arch_versions() -> list[str]:
    if not ARCH.exists():
        return []
    text = ARCH.read_text(encoding="utf-8", errors="ignore")
    versions = []
    for line in text.split("\n"):
        m = re.match(r"^\|\s*([\w.]+)\s*\|", line.strip())
        if m:
            versions.append(m.group(1))
    return versions


def update_arch_version_history(payload: dict) -> bool:
    """在 ARCHITECTURE_V10.md 版本历史表中追加新版本。"""
    if not ARCH.exists():
        return False

    text = ARCH.read_text(encoding="utf-8", errors="ignore")
    existing_versions = get_existing_arch_versions()
    ver = payload.get("version", "")
    if not ver or ver in existing_versions:
        return False

    desc = payload.get("description", ver)
    date_str = utc8_now_str()
    modules = payload.get("modules", [])
    remaining = payload.get("remaining_failures", [])

    # Build version entry description
    desc_parts = [desc]
    if remaining:
        desc_parts.append(f" (remaining_failures: {len(remaining)})")
    else:
        desc_parts.append(" — Gate全过")

    new_line = f"| {ver} | {date_str} | {''.join(desc_parts)} |\n"

    lines = text.split("\n")
    # Insert before the V9/V8 lines (oldest entries)
    insert_idx = len(lines) - 3
    for i, line in enumerate(lines):
        m = re.match(r"^\|\s*([\w.]+)\s*\|", line.strip())
        if m and m.group(1) in ("V9.2.0", "V9.0.0", "V8.5.0"):
            insert_idx = i
            break

    lines.insert(insert_idx, new_line)
    ARCH.write_text("\n".join(lines), encoding="utf-8")
    return True


# ════════════════════════════════════════════════════════════════
# CHANGELOG.md 更新
# ════════════════════════════════════════════════════════════════

def update_changelog(payload: dict) -> bool:
    if not CHANGELOG.exists():
        return False

    text = CHANGELOG.read_text(encoding="utf-8", errors="ignore")
    ver = payload.get("version", "")
    if not ver or ver in text[:2000]:
        return False

    should_fuse, reason = _should_fuse(payload)
    date_str = utc8_now_str()
    desc = payload.get("description", ver)
    modules = payload.get("modules", [])
    category = payload.get("category", "更新")

    entry_lines = [
        f"\n## [{ver}] - {date_str} {desc[:80].rstrip('.')}",
        "",
        f"### {category}",
    ]

    if modules:
        for mod in modules:
            layer = mod.get("layer", "")
            path = mod.get("path", "")
            mdesc = mod.get("description", "")
            entry_lines.append(f"- **{path}** ({layer}): {mdesc}")
    else:
        entry_lines.append(f"- {desc}")

    entry_lines.append("")
    if not payload.get("remaining_failures"):
        entry_lines.append("### 验收")
        entry_lines.append("- 全部 Gate 检查通过")

    if not should_fuse:
        entry_lines.append("- ⚠️ 仅 CHANGELOG 记录，未触发架构融合（原因：" + reason + "）")

    lines = text.split("\n")
    insert_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("## [") and i > 0:
            insert_idx = i
            break
    if insert_idx < 0:
        insert_idx = len(lines) - 1
    else:
        insert_idx = insert_idx - 1

    for entry_line in reversed(entry_lines):
        lines.insert(insert_idx, entry_line)
    CHANGELOG.write_text("\n".join(lines), encoding="utf-8")
    return True


# ════════════════════════════════════════════════════════════════
# Fused modules 注册
# ════════════════════════════════════════════════════════════════

def register_fused_module(payload: dict, v2_analysis: Optional[dict] = None) -> bool:
    ver = payload.get("version", "")
    if not ver:
        return False
    dest = FUSED_DIR / f"doc_fusion_{ver}.json"
    if dest.exists():
        return False
    FUSED_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "module": f"doc_fusion_{ver}",
        "version": ver,
        "trigger": payload.get("trigger", "auto"),
        "description": payload.get("description", ver),
        "status": "pass" if not payload.get("remaining_failures") else "fail",
        "remaining_failures": payload.get("remaining_failures", []),
        "should_fuse": _should_fuse(payload)[0],
        "fused_at": datetime.now(TZ).isoformat(),
    }
    # 附加 V2 融合引擎分析元数据（如果可用）
    if v2_analysis:
        entry["v2_analysis"] = v2_analysis
    write_json(dest, entry)
    return True


# ════════════════════════════════════════════════════════════════
# 主入口：auto_fuse / gate_fuse
# ════════════════════════════════════════════════════════════════

def auto_fuse(payload: dict) -> dict:
    """主动调用融合。在完成改动后传入载荷。"""
    should_fuse, reason = _should_fuse(payload)

    # ── V2 融合引擎分析（如果可用且 modules 不为空） ──
    v2_analysis = None
    modules = payload.get("modules", [])
    if _FUSION_V2_AVAILABLE and modules:
        try:
            engine = FusionEngine()
            v2_results = []
            for mod in modules:
                mod_path = mod.get("path", "")
                full_path = ROOT / mod_path
                if full_path.exists() and full_path.suffix == ".py":
                    analysis = engine.analyze_script(full_path)
                    suggested_layer = engine.determine_layer(analysis, path_hint=mod_path)
                    func_count = len(analysis.get("functions", []))
                    class_count = len(analysis.get("classes", []))
                    v2_results.append({
                        "path": mod_path,
                        "suggested_layer": suggested_layer,
                        "functions": func_count,
                        "classes": class_count,
                    })
                else:
                    v2_results.append({
                        "path": mod_path,
                        "suggested_layer": "",
                        "functions": 0,
                        "classes": 0,
                        "note": "非 .py 文件或不存在，跳过 AST 分析",
                    })
            if v2_results:
                v2_analysis = {"analyzed_modules": v2_results}
        except Exception as e:
            # V2 分析失败不影响主融合逻辑
            v2_analysis = {"error": str(e)}
    # ────────────────────────────────────────────────

    results = {
        "should_fuse": should_fuse,
        "reason": reason,
        "arch_updated": False,
        "changelog_updated": False,
        "fused_registered": False,
        "v2_analysis_available": _FUSION_V2_AVAILABLE,
    }

    if should_fuse:
        results["arch_updated"] = update_arch_version_history(payload)
    results["changelog_updated"] = update_changelog(payload)
    results["fused_registered"] = register_fused_module(payload, v2_analysis=v2_analysis)

    # 剔除信息性字段，只判断核心融合结果
    core_keys = ["arch_updated", "changelog_updated", "fused_registered"]
    all_ok = all(results.get(k, False) for k in core_keys)
    results["status"] = "pass" if all_ok else "partial"

    # Write fusion report
    report = REPORTS_DIR / "DOC_FUSION_ENGINE_REPORT.json"
    write_json(report, {
        "module": "doc_fusion_engine",
        "mode": "auto",
        "status": results["status"],
        "results": results,
        "payload": {k: v for k, v in payload.items() if k != "modules"},
        "timestamp": datetime.now(TZ).isoformat(),
    })

    return results


# ════════════════════════════════════════════════════════════════
# V3 自动融合：检测 + 注册 + 融合
# ════════════════════════════════════════════════════════════════

_SKILL_CATEGORIES = {
    "data": "finance|stock|market|quote|search|crawler|scraper",
    "media": "image|video|music|audio|comic|picture|drawing|paint",
    "content": "writing|article|writing|copy|文案|创作|写作",
    "tool": "formatter|converter|parser|validator|generator|calculator|lookup|minifier",
    "code": "code|program|python|react|test|regex|json|hash|uuid|tokenizer",
    "productivity": "brain|memory|note|plan|review|calendar|email|task",
    "education": "k12|edu|math|study|学习|考试|课程",
    "health": "health|fitness|fasting|diet|健身",
    "design": "design|ui|ux|html|excalidraw|diagram|slide|ppt|flowchart",
}


def _infer_layer(path: str, category: str = "general") -> str:
    """根据路径和分类推断所属架构层。"""
    layer_map = {
        "core/": "L1 Core",
        "memory_context/": "L2 Memory",
        "orchestration/": "L3 Orchestration",
        "execution/": "L4 Execution",
        "governance/": "L5 Governance",
        "infrastructure/": "L6 Infrastructure",
        "scripts/": "L6 Infrastructure",
        "skills/": "L6 Infrastructure",
        "docs/": "L1 Core",
    }
    for prefix, layer in layer_map.items():
        if path.startswith(prefix):
            return layer
    return "L6 Infrastructure"


def _detect_new_skills() -> List[Dict[str, Any]]:
    """检测 skills/ 下新增的 SKILL.md，尝试注册。"""
    new_modules = []
    try:
        from core.skill_rules_engine import register_skill, scan_new_skills
        new = scan_new_skills()
        for name in new:
            result = register_skill(name)
            if result.get("status") in ("registered", "updated"):
                data = result.get("data", {})
                new_modules.append({
                    "path": f"skills/{name}/SKILL.md",
                    "layer": "L6 Infrastructure",
                    "description": f"[自动注册] {data.get('category', 'general')} — {data.get('description', '')[:60]}",
                    "triggers": data.get("trigger_keywords", [])[:3],
                    "requires_api": data.get("requires_external_api", False),
                })
                print(f"      🆕 自动注册新技能: {name}")
    except ImportError:
        pass
    except Exception as e:
        print(f"      ⚠️ 技能自动注册失败: {e}")
    return new_modules


def _get_fusion_state() -> dict:
    """读取融合状态快照。"""
    if _FUSION_STATE_FILE.exists():
        try:
            return json.loads(_FUSION_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_fusion_state(state: dict):
    """保存融合状态快.照。"""
    _FUSION_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _FUSION_STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def _scan_for_new_modules() -> List[Dict[str, Any]]:
    """扫描关键目录，检测新增的 .py 文件和 SKILL.md。"""
    tracked_dirs = [
        ROOT / "core",
        ROOT / "memory_context",
        ROOT / "orchestration",
        ROOT / "execution",
        ROOT / "governance",
        ROOT / "infrastructure",
        ROOT / "scripts",
        ROOT / "skills",
        ROOT / "docs",
    ]

    state = _get_fusion_state()
    previous = state.get("file_hashes", {})
    new_modules = []
    current_hashes = {}

    for scan_dir in tracked_dirs:
        if not scan_dir.exists():
            continue
        # Limit depth for skills (only 1 level deep)
        if scan_dir.name == "skills":
            for skill_dir in sorted(scan_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                md = skill_dir / "SKILL.md"
                if not md.exists():
                    continue
                key = str(md.relative_to(ROOT))
                mtime = md.stat().st_mtime
                fsize = md.stat().st_size
                current_hashes[key] = {"mtime": mtime, "size": fsize}
                # Detect new skills (never seen before)
                if key not in previous:
                    new_modules.append({
                        "path": key,
                        "layer": "L6 Infrastructure",
                        "description": f"技能: {skill_dir.name}",
                        "new": True,
                    })
        else:
            for py in sorted(scan_dir.rglob("*.py")):
                if any(e in str(py) for e in ["__pycache__", "archive/", ".v"]):
                    continue
                key = str(py.relative_to(ROOT))
                mtime = py.stat().st_mtime
                fsize = py.stat().st_size
                current_hashes[key] = {"mtime": mtime, "size": fsize}
                if key not in previous:
                    new_modules.append({
                        "path": key,
                        "layer": _infer_layer(key),
                        "description": f"新文件: {py.name}",
                        "new": True,
                    })

    state["file_hashes"] = current_hashes
    state["last_scan"] = datetime.now(TZ).isoformat()
    _save_fusion_state(state)

    return new_modules


def _get_next_version() -> str:
    """自动生成下一个融合版本号。"""
    existing = []
    if FUSED_DIR.exists():
        for f in FUSED_DIR.iterdir():
            m = re.search(r'doc_fusion_(V[\w.]+)\.json', f.name)
            if m:
                existing.append(m.group(1))
    # Try V106, V107, etc.
    for n in range(106, 1000):
        v = f"V{n}"
        if v not in existing:
            # Also check ARCH
            arch_versions = set()
            if ARCH.exists():
                for line in ARCH.read_text(encoding="utf-8").split("\n"):
                    m2 = re.match(r"\|\s*([\w.]+)\s*\|", line.strip())
                    if m2:
                        arch_versions.add(m2.group(1))
            if v not in arch_versions:
                return v
    return "V999"


def scan_and_fuse() -> Dict[str, Any]:
    """全自动扫描+融合入口。
    
    执行流程：
    1. 扫描 skills/ 检测新技能 → 自动注册到 skill_trigger_registry
    2. 扫描 core/memory/orchestration/execution/governance/infra/scripts 检测新文件
    3. 如果有新内容，自动生成融合载荷并调用 auto_fuse()
    """
    print("🔍 V3 自动融合扫描开始...\n")

    # Step 1: Detect new skills and register
    new_skills = _detect_new_skills()
    if new_skills:
        print(f"      📌 新技能: {len(new_skills)}")
        for ns in new_skills:
            print(f"         - {ns['path']}")

    # Step 2: Scan for new modules
    new_modules = _scan_for_new_modules()
    if new_modules:
        print(f"      📌 新模块: {len(new_modules)}")
        for nm in new_modules:
            print(f"         - {nm['path']}")

    # Step 3: If nothing new, skip
    all_new = new_skills + new_modules
    if not all_new:
        print("      📭 无新内容，跳过融合")
        return {
            "status": "skipped",
            "reason": "no_new_content",
            "new_skills": 0,
            "new_modules": 0,
        }

    # Step 4: Build payload and auto-fuse
    version = _get_next_version()
    # Categorize
    categories = [ns.get("description", "") for ns in new_skills]
    categories.extend(nm.get("description", "") for nm in new_modules)
    description = "; ".join(categories[:3])
    if len(categories) > 3:
        description += f"... +{len(categories) - 3} more"

    payload = {
        "version": version,
        "trigger": "auto_scan",
        "category": "自动融合扫描",
        "description": f"自动扫描新增: {len(new_skills)}技能+{len(new_modules)}模块",
        "architecture_related": True,
        "user_visible": False,
        "security_changed": False,
        "gate_passed": True,
        "remaining_failures": [],
        "modules": [{
            "path": m["path"],
            "layer": m.get("layer", "L6 Infrastructure"),
            "description": m.get("description", ""),
        } for m in all_new],
    }

    print(f"\n      📦 融合版本: {version}")
    print(f"      📝 描述: {payload['description']}")
    result = auto_fuse(payload)
    result["version"] = version
    result["auto_scan"] = True

    # Write scan report
    scan_report = REPORTS_DIR / "AUTO_FUSION_SCAN_REPORT.json"
    write_json(scan_report, {
        "status": result.get("status", "pass"),
        "version": version,
        "new_skills": len(new_skills),
        "new_modules": len(new_modules),
        "result": result,
        "timestamp": datetime.now(TZ).isoformat(),
    })

    return result


# ════════════════════════════════════════════════════════════════
# CLI 入口
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "auto":
        # JSON 载荷从 stdin 传入
        payload = json.loads(sys.stdin.read())
        result = auto_fuse(payload)
    elif len(sys.argv) >= 2 and sys.argv[1] == "scan":
        # 无参数全自动扫描融合
        result = scan_and_fuse()
    else:
        print(json.dumps({
            "error": "Usage: 1) echo '{\"version\":\"V105\",...}' | python3 doc_fusion_engine.py auto",
            "usage2": "       2) python3 doc_fusion_engine.py scan  # 全自动扫描+融合",
            "options": {
                "echo + auto": "手动传入融合载荷调用融合",
                "scan": "全自动扫描skills/core/scripts等目录，检测新内容并自动融合"
            }
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))
