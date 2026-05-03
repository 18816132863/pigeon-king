#!/usr/bin/env python3
"""
V99.5 — 将六层外目录迁移到架构层 + 兼容转发层

迁移映射：
  agent_kernel/ (41文件)  → orchestration/agent_kernel/
  config/ (7文件)          → infrastructure/config/
  ops/ (3文件)             → governance/ops/
  application/ (7文件)     → execution/application/
  domain/ (4文件)          → core/domain/
  evaluation/ (3文件)      → evaluation/ (已在目标层，但需要确认)
"""
from __future__ import annotations

import os, sys, shutil, time, json
from pathlib import Path

ROOT = Path.cwd()
REPORTS = ROOT / "reports"

os.environ["NO_EXTERNAL_API"] = "true"
os.environ["NO_REAL_SEND"] = "true"
os.environ["NO_REAL_PAYMENT"] = "true"
os.environ["NO_REAL_DEVICE"] = "true"

# 迁移映射: 旧目录 → 新目录
MIGRATIONS = {
    "agent_kernel": "orchestration/agent_kernel",
    "config": "infrastructure/config",
    "ops": "governance/ops",
    "application": "execution/application",
    "domain": "core/domain",
    "evaluation": "governance/evaluation",
}

def safe_jsonable(obj):
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): safe_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [safe_jsonable(x) for x in obj]
    return str(obj)

def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(safe_jsonable(data), ensure_ascii=False, indent=2))

class DirectoryMigrator:
    def __init__(self):
        self.log = []
        self.errors = []

    def migrate(self, old_name: str, new_path: str) -> dict:
        result = {
            "old_dir": old_name,
            "new_dir": new_path,
            "files_moved": [],
            "compatibility_files": [],
            "files_total": 0,
            "status": "pending",
            "errors": [],
        }
        old_dir = ROOT / old_name
        new_dir = ROOT / new_path

        if not old_dir.is_dir():
            result["status"] = "skipped"
            result["errors"].append(f"Old dir not found: {old_name}")
            return result

        # 1. 创建目标目录
        new_dir.mkdir(parents=True, exist_ok=True)
        if old_name != new_path.split("/")[-1]:
            # 如果旧名和最终目录名不同，创建子目录
            target_dir = new_dir
        else:
            target_dir = new_dir

        target_dir.mkdir(parents=True, exist_ok=True)

        # 2. 收集所有 .py 文件（除 __pycache__ 和 __init__.py）
        py_files = sorted(old_dir.glob("*.py"))
        py_files = [f for f in py_files if f.name != "__init__.py"]

        # 深度扫描子目录
        all_files = []
        for ext in ["*.py", "*.json", "*.yaml", "*.yml", "*.md", "*.txt", "*.example"]:
            all_files.extend(old_dir.rglob(ext))
        all_files = [f for f in all_files if "__pycache__" not in str(f) and f.suffix == ".py"]

        for f in all_files:
            rel = f.relative_to(old_dir)
            dest = target_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)

            if f.is_file() and f.name != "__init__.py":
                shutil.copy2(f, dest)
                result["files_moved"].append({
                    "name": str(rel),
                    "from": str(f.relative_to(ROOT)),
                    "to": str(dest.relative_to(ROOT)),
                    "size": f.stat().st_size,
                })

        # 3. 创建 __init__.py（确保包可导入）
        init_file = target_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f"# {new_path} package\n# Migrated from {old_name}/\n")

        # 4. 创建兼容转发层（旧位置 → 新位置）
        # 对于 agent_kernel: from orchestration.agent_kernel.xxx import *
        old_package = old_name
        new_import_path = new_path.replace("/", ".")

        compat_count = 0
        for f in py_files:
            compat_source = target_dir / f.name
            if not compat_source.exists():
                continue

            # 读取源文件的 __all__ 或所有顶层名字
            compat_file = old_dir / f.name

            # 生成兼容转发：旧文件变成一行 import
            compat_line = f"from {new_import_path}.{f.stem} import *  # noqa: F401,F403\n"

            # 检查兼容文件是否需要重写
            old_content = compat_file.read_text(encoding="utf-8", errors="ignore")
            if old_content.strip() != compat_line.strip():
                compat_file.write_text(compat_line, encoding="utf-8")
                compat_count += 1

        result["compatibility_rewrites"] = compat_count
        result["files_total"] = len(result["files_moved"])
        result["status"] = "ok"

        self.log.append(result)
        return result

    def verify_imports(self, old_name: str) -> dict:
        """验证旧 import 在新位置是否可用"""
        new_path = MIGRATIONS[old_name]
        result = {
            "old_dir": old_name,
            "new_dir": new_path,
            "import_test": [],
            "all_ok": True,
        }

        sys.path.insert(0, str(ROOT))
        new_import_path = new_path.replace("/", ".")

        # 测试新路径导入
        try:
            mod = __import__(f"{new_import_path}.__init__")
            result["import_test"].append({
                "path": f"{new_import_path}",
                "importable": True,
            })
        except Exception as e:
            result["import_test"].append({
                "path": f"{new_import_path}",
                "importable": False,
                "error": str(e)[:100],
            })
            result["all_ok"] = False

        # 测试旧路径兼容导入
        try:
            mod = __import__(f"{old_name}.__init__")
            result["import_test"].append({
                "path": f"{old_name}",
                "importable": True,
                "note": "compatibility layer works",
            })
        except Exception as e:
            result["import_test"].append({
                "path": f"{old_name}",
                "importable": False,
                "error": str(e)[:100],
                "note": "compatibility layer failed",
            })
            result["all_ok"] = False

        return result


def main():
    print("=" * 65)
    print("  V99.5 — 目录迁移到架构层")
    print("=" * 65)

    migrator = DirectoryMigrator()
    all_results = []
    import_verifications = []

    # 步骤 1: 迁移
    for old_name, new_path in MIGRATIONS.items():
        if old_name == "evaluation":
            # evaluation 已经有 __init__.py，特殊处理
            old_dir = ROOT / "evaluation"
            new_dir = ROOT / "governance" / "evaluation"
            if old_dir.is_dir():
                # 先确保目标有 __init__.py
                new_dir.mkdir(parents=True, exist_ok=True)
                py_files = [f for f in old_dir.glob("*.py") if f.name != "__init__.py"]
                for f in py_files:
                    shutil.copy2(f, new_dir / f.name)

                # 创建兼容转发
                for f in py_files:
                    old_path = old_dir / f.name
                    old_path.write_text(
                        f"from governance.evaluation.{f.stem} import *  # noqa: F401,F403\n",
                        encoding="utf-8"
                    )

                result = {
                    "old_dir": "evaluation", "new_dir": "governance/evaluation",
                    "files_moved": [{"name": f.name} for f in py_files],
                    "files_total": len(py_files), "status": "ok"
                }
            else:
                result = {"old_dir": "evaluation", "status": "skipped"}
        else:
            result = migrator.migrate(old_name, new_path)

        all_results.append(result)
        print(f"  {'✅' if result['status']=='ok' else '⚠️'} {old_name}/ → {new_path}/ ({result.get('files_total', 0)} files)")

        # 验证
        if result["status"] == "ok":
            ver = migrator.verify_imports(old_name)
            import_verifications.append(ver)

    # 步骤 2: 验证结果
    all_ok = all(r["status"] == "ok" or r["status"] == "skipped" for r in all_results)
    all_import_ok = all(v["all_ok"] for v in import_verifications)

    # 步骤 3: 生成报告
    report = {
        "version": "V99.5",
        "status": "pass" if (all_ok and all_import_ok) else "partial",
        "migrations": all_results,
        "import_verifications": import_verifications,
        "all_migrations_ok": all_ok,
        "all_imports_ok": all_import_ok,
        "remaining_failures": [],
        "note": "V99.5 目录迁移。旧路径保留兼容转发层，新路径在六层架构内。",
    }

    if not all_ok:
        report["remaining_failures"].append("some_migrations_failed")
    if not all_import_ok:
        report["remaining_failures"].append("some_import_verifications_failed")

    write_json(REPORTS / "V99_5_DIRECTORY_MIGRATION_GATE.json", report)

    print(f"\n  status: {report['status']}")
    print(f"  remaining_failures: {report['remaining_failures']}")
    print(f"  total files moved: {sum(r.get('files_total', 0) for r in all_results)}")
    print(f"  report: {REPORTS / 'V99_5_DIRECTORY_MIGRATION_GATE.json'}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
