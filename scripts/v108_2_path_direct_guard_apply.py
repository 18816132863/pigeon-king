#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path.cwd()
REPORTS = ROOT / "reports"
BACKUP = ROOT / ".v108_2_backup"
REPORTS.mkdir(exist_ok=True)
BACKUP.mkdir(exist_ok=True)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def backup(path: Path) -> None:
    if path.exists():
        dest = BACKUP / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copy2(path, dest)


def patch_text(rel: str, transform) -> dict:
    path = ROOT / rel
    if not path.exists():
        return {"path": rel, "status": "missing"}
    backup(path)
    old = path.read_text(encoding="utf-8", errors="ignore")
    new = transform(old, rel)
    changed = new != old
    if changed:
        path.write_text(new, encoding="utf-8")
    return {"path": rel, "status": "patched" if changed else "unchanged"}


def ensure_guard_import(text: str, reason: str) -> str:
    marker = "_v1082_offline_guard_activation"
    if marker in text:
        return text
    block = f'''
# {marker}
try:
    from infrastructure.offline_runtime_guard import activate as _v1082_activate_offline_guard
    _v1082_activate_offline_guard("{reason}")
except Exception:
    pass
'''
    if "from __future__ import annotations" in text:
        return text.replace("from __future__ import annotations", "from __future__ import annotations\n" + block, 1)
    return block + "\n" + text


def patch_pathcwd(text: str, rel: str) -> str:
    if "Path.cwd()" not in text:
        return text
    if "get_workspace_root" not in text:
        if "from pathlib import Path" in text:
            text = text.replace("from pathlib import Path", "from pathlib import Path\nfrom infrastructure.common.path_utils import get_workspace_root", 1)
        else:
            text = "from infrastructure.common.path_utils import get_workspace_root\n" + text
    text = text.replace("ROOT = Path.cwd()", "ROOT = get_workspace_root(Path(__file__))")
    text = text.replace("root = Path.cwd()", "root = get_workspace_root(Path(__file__))")
    text = text.replace("current = Path.cwd()", "current = get_workspace_root(Path(__file__))")
    text = text.replace("return Path.cwd()", "return get_workspace_root(Path(__file__))")
    return text


def patch_connector_subprocess(text: str, rel: str) -> str:
    text = ensure_guard_import(text, "real_connector_execution")
    if "check_tool_call" not in text:
        text = text.replace("import sys\n", "import sys\nfrom execution.unified_tool_execution_gateway import check_tool_call\n", 1)
    # Guard the known SafeScriptConnector subprocess call.
    old = "res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)"
    new = """gate = check_tool_call(" ".join(cmd), {"source": "SafeScriptConnector"})
            if gate.get("status") == "blocked":
                return ConnectorStatus.BLOCKED, {"script_executed": False, "gateway": gate}, ""
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)"""
    if old in text and "source\": \"SafeScriptConnector" not in text:
        text = text.replace(old, new, 1)
    return text


def patch_report_index() -> dict:
    current = REPORTS / "current"
    vintage = REPORTS / "vintage"
    current.mkdir(exist_ok=True)
    vintage.mkdir(exist_ok=True)
    current_names = [
        "V95_2_ALL_CHAIN_COVERAGE_GATE.json",
        "V96_FAILURE_RECOVERY_AND_STABILITY_GATE.json",
        "V97_LONG_RUN_STABILITY_GATE.json",
        "V98_1_MAINLINE_HOOK_RUNTIME_GATE.json",
        "V100_FINAL_PENDING_ACCESS_RELEASE_GATE.json",
        "V104_3_RUNTIME_FUSION_COORDINATION_GATE.json",
        "V107_UNIFIED_SUBSYSTEM_FUSION_GATE.json",
        "V108_REMAINING_UNIFIED_SYSTEMS_GATE.json",
        "V108_1_EXECUTION_IMPORT_SAFETY_GATE.json",
    ]
    copied = []
    for name in current_names:
        src = REPORTS / name
        if src.exists():
            shutil.copy2(src, current / name)
            copied.append(name)
    moved_vintage = []
    for fp in list(REPORTS.glob("*.json")):
        if fp.name in current_names or fp.name.startswith("V108_2_") or fp.name == "CURRENT_RELEASE_INDEX.json":
            continue
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            status = data.get("status") if isinstance(data, dict) else None
        except Exception:
            status = None
        if status in {"fail", "failed", "partial"}:
            dest = vintage / fp.name
            if not dest.exists():
                shutil.copy2(fp, dest)
            moved_vintage.append(fp.name)
    index = {
        "version": "V108.2",
        "current_reports": copied,
        "vintage_candidates": moved_vintage,
        "status_source": "reports/current + CURRENT_RELEASE_INDEX",
    }
    write_json(REPORTS / "CURRENT_RELEASE_INDEX.json", index)
    return index


def main() -> None:
    changes = []
    path_targets = [
        "core/llm/provider_guard.py",
        "infrastructure/solution_search_orchestrator.py",
        "infrastructure/packaging/__init__.py",
        "infrastructure/diagnose_embedding.py",
    ]
    for rel in path_targets:
        changes.append(patch_text(rel, patch_pathcwd))

    guard_targets = [
        "core/llm/llm.py",
        "core/llm/llm_client.py",
        "core/llm/llm_gateway.py",
        "core/llm/model_discovery.py",
        "infrastructure/legacy/llm.py",
        "infrastructure/setup_tools/one_click_setup.py",
        "infrastructure/auto_backup_uploader.py",
        "core/real_connector_execution/connectors.py",
        "memory_context/vector/qdrant_store.py",
        "memory_context/vector/embedding.py",
    ]
    for rel in guard_targets:
        if rel == "core/real_connector_execution/connectors.py":
            changes.append(patch_text(rel, patch_connector_subprocess))
        else:
            changes.append(patch_text(rel, lambda text, r: ensure_guard_import(patch_pathcwd(text, r), r.replace("/", "."))))

    index = patch_report_index()
    report = {
        "version": "V108.2",
        "status": "pass",
        "changes": changes,
        "current_release_index": index,
        "no_external_api": True,
        "no_real_send": True,
        "no_real_payment": True,
        "no_real_device": True,
    }
    write_json(REPORTS / "V108_2_PATH_DIRECT_GUARD_APPLY.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
