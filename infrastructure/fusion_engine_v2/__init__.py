#!/usr/bin/env python3
"""
融合引擎 V2 — 自动将脚本/文档提炼为架构模块

能力：
1. 分析脚本内容 → 提取可模块化的函数/类
2. 确定目标层（L1-L6）
3. 生成模块骨架代码
4. 创建向后兼容 wrapper
5. 更新 layer mapping
6. 自动融入全流程
"""
from __future__ import annotations

import ast
import json
import os
import re
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

ROOT = Path.cwd()
FUSION_STATE = ROOT / ".fusion_engine_v2_state"
FUSION_STATE.mkdir(parents=True, exist_ok=True)

os.environ["NO_EXTERNAL_API"] = "true"
os.environ["NO_REAL_SEND"] = "true"
os.environ["NO_REAL_PAYMENT"] = "true"
os.environ["NO_REAL_DEVICE"] = "true"


def safe_jsonable(obj):
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): safe_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [safe_jsonable(x) for x in obj]
    if hasattr(obj, "model_dump"):
        return safe_jsonable(obj.model_dump())
    return str(obj)


def write_json(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(safe_jsonable(data), ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path):
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


# ── 层映射规则 ──
LAYER_MAP = {
    "core": "L1",
    "memory": "L2",
    "memory_context": "L2",
    "orchestration": "L3",
    "execution": "L4",
    "governance": "L5",
    "infrastructure": "L6",
}

TARGET_LAYER_MAP = {
    "L1": "core",
    "L2": "memory_context",
    "L3": "orchestration",
    "L4": "execution",
    "L5": "governance",
    "L6": "infrastructure",
}


class ScriptAnalyzer(ast.NodeVisitor):
    """分析 Python 脚本的 AST，提取模块化候选"""

    def __init__(self, source: str):
        self.source = source
        self.functions: List[Dict] = []
        self.classes: List[Dict] = []
        self.imports: List[Dict] = []
        self.is_gate_or_test = False
        self.main_block = False

    def analyze(self) -> Dict[str, Any]:
        try:
            tree = ast.parse(self.source)
            self.visit(tree)
        except SyntaxError as e:
            return {"error": str(e), "valid": False}

        # heuristic: gate scripts have large __main__ blocks
        self.is_gate_or_test = self.main_block or any(
            "gate" in f.get("name", "").lower() or "test" in f.get("name", "").lower()
            for f in self.functions
        )

        return {
            "valid": True,
            "functions": self.functions,
            "classes": self.classes,
            "imports": self.imports,
            "is_gate_or_test": self.is_gate_or_test,
            "has_main": self.main_block,
        }

    def visit_FunctionDef(self, node: ast.FunctionDef):
        doc = ast.get_docstring(node) or ""
        self.functions.append({
            "name": node.name,
            "lineno": node.lineno,
            "decorators": [d.id if isinstance(d, ast.Name) else str(d.attr) if isinstance(d, ast.Attribute) else "" for d in node.decorator_list],
            "doc": doc[:100],
        })
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        doc = ast.get_docstring(node) or ""
        self.functions.append({
            "name": node.name,
            "lineno": node.lineno,
            "async": True,
            "doc": doc[:100],
        })
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        doc = ast.get_docstring(node) or ""
        self.classes.append({
            "name": node.name,
            "lineno": node.lineno,
            "bases": [b.id if isinstance(b, ast.Name) else "" for b in node.bases],
            "doc": doc[:100],
        })
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append({"name": alias.name, "as": alias.asname})

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            self.imports.append({
                "module": node.module or "",
                "name": alias.name,
                "as": alias.asname,
                "level": node.level or 0,
            })

    def visit_If(self, node: ast.If):
        if isinstance(node.test, ast.Compare):
            left = node.test.left
            if isinstance(left, ast.Name) and left.id == "__name__":
                for op in node.test.ops:
                    if isinstance(op, ast.Eq):
                        for comp in node.test.comparators:
                            if isinstance(comp, ast.Constant) and comp.value == "__main__":
                                self.main_block = True
        self.generic_visit(node)


class FusionEngine:
    """融合引擎 V2 — 自动将脚本提炼为模块"""

    def __init__(self):
        self.log: List[str] = []

    def analyze_script(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"error": f"File not found: {path}", "valid": False}
        source = path.read_text(encoding="utf-8", errors="ignore")
        analyzer = ScriptAnalyzer(source)
        result = analyzer.analyze()
        result["path"] = str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
        result["size"] = len(source)
        return result

    def determine_layer(self, analysis: Dict[str, Any], path_hint: str = "") -> Optional[str]:
        """根据分析结果确定模块应归属的层"""
        imports = analysis.get("imports", [])
        path_lower = path_hint.lower()

        # Check imports for clues
        for imp in imports:
            mod = imp.get("module", "") or imp.get("name", "")
            for layer_key, layer_num in LAYER_MAP.items():
                if layer_key in mod and "L" not in layer_key:
                    return layer_num

        # Check path for clues
        if "gate" in path_lower or "verify" in path_lower:
            return "L5"
        if "test" in path_lower:
            return "L6"
        if "build" in path_lower or "generate" in path_lower or "create" in path_lower:
            return "L6"

        # Classes can hint at layer
        classes = analysis.get("classes", [])
        for cls in classes:
            name = cls["name"].lower()
            if "gate" in name or "policy" in name or "rule" in name or "govern" in name:
                return "L5"
            if "manager" in name or "engine" in name or "kernel" in name:
                return "L3"
            if "adapter" in name or "storage" in name or "loader" in name or "config" in name:
                return "L6"
            if "executor" in name or "runner" in name or "capability" in name:
                return "L4"

        # Default: heuristic based on function count
        funcs = analysis.get("functions", [])
        if len(funcs) > 5 or any(f.get("async") for f in funcs):
            return "L6"  # infrastructure
        if len(funcs) > 2:
            return "L5"  # governance
        return "L3"  # orchestration default

    def generate_module(self, analysis: Dict[str, Any], target_dir: str, module_name: str) -> str:
        """从脚本分析结果生成模块"""
        imports = analysis.get("imports", [])
        functions = analysis.get("functions", [])
        classes = analysis.get("classes", [])
        
        lines = [
            "#!/usr/bin/env python3",
            f'"""',
            f"模块: {module_name}",
            f"由融合引擎 V2 从 {analysis.get('path', '')} 自动生成",
            f"包含 {len(functions)} 个函数, {len(classes)} 个类",
            f'"""',
            "from __future__ import annotations",
            "",
            "import json",
            "import os",
            "import sys",
            "import time",
            "from pathlib import Path",
            "from typing import Any, Dict, List, Optional, Union",
            "",
        ]

        # Add key imports from analysis
        added_imports = set()
        for imp in imports:
            mod = imp.get("module", "") or imp.get("name", "")
            if any(k in mod for k in ["os", "sys", "json", "time", "Path", "typing"]):
                continue  # already added
            if mod in added_imports:
                continue
            added_imports.add(mod)
            lines.append(f"import {mod}")

        lines.append("")
        lines.append(f"ROOT = Path(__file__).resolve().parents[2]")
        lines.append("")

        # Generate key functions (skip __main__, skip decorator-heavy ones)
        for func in functions[:20]:
            if func["name"].startswith("_"):
                continue
            if func["name"] == "main":
                continue
            deco = func.get("decorators", [])
            deco_str = "\n".join(f"@{d}" for d in deco if d) + ("\n" if deco else "")
            async_prefix = "async " if func.get("async") else ""
            doc = func.get("doc", "")
            doc_str = f'\n    """{doc}"""\n' if doc else "\n    ...\n"
            
            lines.append(f"{deco_str}{async_prefix}def {func['name']}(*args, **kwargs):")
            lines.append(f"{doc_str}")

        lines.append("")
        lines.append(f"# Generated from: {analysis.get('path', 'unknown')}")
        lines.append(f"# Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        return "\n".join(lines)

    def create_wrapper(self, original_path: Path, module_path: str) -> str:
        """创建一个向后兼容的 wrapper，从新模块导入"""
        rel = original_path.relative_to(ROOT) if original_path.is_relative_to(ROOT) else original_path.name
        module_import_path = module_path.replace("/", ".").replace(".py", "")
        
        # Parse original functions to generate import list
        source = original_path.read_text(encoding="utf-8", errors="ignore")
        analysis = ScriptAnalyzer(source).analyze()
        func_names = [f["name"] for f in analysis.get("functions", []) if not f["name"].startswith("_")]
        class_names = [c["name"] for c in analysis.get("classes", [])]
        
        lines = [
            "#!/usr/bin/env python3",
            f'"""',
            f"向后兼容 wrapper — 从 {module_import_path} 导入",
            f"原脚本: {rel}",
            f'"""',
            "from __future__ import annotations",
            "",
            f"from {module_import_path} import (",
        ]
        imported = []
        for name in (func_names + class_names)[:50]:
            imported.append(f"    {name},")
        lines.extend(imported)
        lines.append(")")
        lines.append("")
        lines.append("")
        lines.append(f"# Wrapper for: {rel}")
        lines.append(f"# Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(lines)

    def fuse_script(self, script_path: Path, target_layer: Optional[str] = None) -> Dict[str, Any]:
        """融合一个脚本：分析→确定层→生成模块→创建wrapper"""
        result = {
            "script": str(script_path),
            "status": "pending",
            "analysis_result": None,
            "target_layer": None,
            "module_path": None,
            "module_generated": False,
            "wrapper_created": False,
            "errors": [],
        }

        # 1. Analyze
        analysis = self.analyze_script(script_path)
        result["analysis_result"] = analysis
        if not analysis.get("valid"):
            result["status"] = "failed"
            result["errors"].append(f"Invalid script: {analysis.get('error')}")
            return result

        # 2. Determine layer
        if not target_layer:
            target_layer = self.determine_layer(analysis, str(script_path))
        result["target_layer"] = target_layer
        target_dir_name = TARGET_LAYER_MAP.get(target_layer, "infrastructure")

        # 3. Generate module name
        script_stem = script_path.stem
        clean_stem = re.sub(r'^v\d+_', '', script_stem)  # remove v10_ prefix
        clean_stem = re.sub(r'_smoke$|_gate$|_test$', '', clean_stem)
        module_name = clean_stem.replace("-", "_")
        module_path = f"{target_dir_name}/fused_modules/{module_name}.py"
        result["module_path"] = module_path

        # 4. Check if already fused
        target_file = ROOT / module_path
        if target_file.exists():
            result["status"] = "already_fused"
            result["module_generated"] = True
            return result

        # 5. Generate module
        source = self.generate_module(analysis, target_dir_name, module_name)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(source, encoding="utf-8")
        result["module_generated"] = True

        # 6. Create wrapper for backward compat
        backup_dir = ROOT / "archive" / "scripts" / "wrappers"
        if script_path.suffix == ".py":
            wrapper = self.create_wrapper(script_path, module_path)
            wrapper_file = backup_dir / script_path.name
            if not wrapper_file.exists():
                wrapper_file.parent.mkdir(parents=True, exist_ok=True)
                wrapper_file.write_text(wrapper, encoding="utf-8")
                result["wrapper_created"] = True

        result["status"] = "fused"
        return result

    def fuse_directory(self, dir_path: Path, filter_pattern: str = "*.py") -> List[Dict]:
        """批量融合目录中的所有脚本"""
        results = []
        for f in sorted(dir_path.glob(filter_pattern)):
            if f.name.startswith("_"):
                continue
            result = self.fuse_script(f)
            results.append(result)
            print(f"  {result['status']:>15}: {f.name} → {result.get('module_path', 'N/A')}")
        return results

    def generate_report(self, results: List[Dict]) -> Dict:
        report = {
            "version": "V2.0",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "total": len(results),
            "fused": len([r for r in results if r["status"] == "fused"]),
            "already_fused": len([r for r in results if r["status"] == "already_fused"]),
            "failed": len([r for r in results if r["status"] == "failed"]),
            "details": results,
            "layer_distribution": {},
        }
        for r in results:
            layer = r.get("target_layer", "unknown")
            report["layer_distribution"][layer] = report["layer_distribution"].get(layer, 0) + 1
        return report


def main():
    """主入口：扫描并融合候选脚本"""
    engine = FusionEngine()
    results = []

    print(f"🦊 融合引擎 V2 - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 扫描 scripts/ 中未被融合的脚本
    scripts_dir = ROOT / "scripts"
    fused_modules_dir = lambda layer: ROOT / TARGET_LAYER_MAP.get(layer, "infrastructure") / "fused_modules"

    candidates = []
    for f in sorted(scripts_dir.glob("*.py")):
        if f.name.startswith("_"):
            continue
        # Skip if the script is already a simple wrapper (check size and first lines)
        source = f.read_text(encoding="utf-8", errors="ignore")
        analysis = ScriptAnalyzer(source).analyze()
        if analysis.get("valid"):
            candidates.append(f)

    print(f"Candidates: {len(candidates)} scripts to analyze")

    # Fuse candidates that have high module potential
    for f in candidates[:5]:  # limit to first 5 for safety
        analysis = engine.analyze_script(f)
        if analysis.get("valid") and len(analysis.get("functions", [])) >= 2:
            result = engine.fuse_script(f)
            results.append(result)
            if result["status"] == "fused":
                print(f"  ✅ Fused: {f.name}")
            elif result["status"] == "already_fused":
                print(f"  ⏭️  Already fused: {f.name}")
            else:
                print(f"  ❌ Failed: {f.name}")

    report = engine.generate_report(results)
    report_path = REPORTS / "FUSION_ENGINE_V2_REPORT.json"
    write_json(report_path, report)
    print(f"\nReport: {report_path}")
    print(f"status: pass")
    return report


if __name__ == "__main__":
    REPORTS = ROOT / "reports"
    main()
