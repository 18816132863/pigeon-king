"""
Solution Search Orchestrator — V91 离线可运行版。

规则：
- OFFLINE_MODE=true / NO_EXTERNAL_API=true 时，禁止调用外部大模型、联网搜索、MCP、connector、
  Deep Research、requests/http。
- 降级为本地文件搜索：memory/ memory_context/ reports/ docs/ + capability/workflow registry
  + 本地 .md .json .txt .py 文件。
- 动作语义固定为 analyze / prepare / dry-run，不可被识别为 unknown 或 commit 类动作。
- 找不到结果也必须返回 status=ok（不抛 gateway_error）。
- 所有调用写 append-only audit。
- 不允许真实支付、签署、外发、身份承诺、物理致动、破坏性动作。
"""
from __future__ import annotations
import json
import os
import re
import time
from pathlib import Path
from infrastructure.common.path_utils import get_workspace_root
from dataclasses import dataclass, field
from typing import Any


# ── 离线探测 ──────────────────────────────────────────────
_OFFLINE_MODE = os.environ.get("OFFLINE_MODE", "1") in ("1", "true", "yes", "True")
_NO_EXTERNAL_API = os.environ.get("NO_EXTERNAL_API", "1") in ("1", "true", "yes", "True")
_WORKSPACE = Path(os.environ.get("WORKSPACE", "/home/sandbox/.openclaw/workspace"))

# ── 审计（自包含，不依赖 offline_mode 模块避免循环导入）───
_AUDIT_PATH = _WORKSPACE / "governance" / "audit" / "solution_search_audit.jsonl"

def _audit(level: str, message: str, **detail) -> None:
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_AUDIT_PATH, "a") as f:
        f.write(json.dumps({
            "ts": time.time(), "level": level, "module": "solution_search_orchestrator",
            "message": message, "detail": detail,
        }, ensure_ascii=False) + "\n")


# ── 常量 ──────────────────────────────────────────────────
_SEARCH_DIRS = ["memory", "memory_context", "reports", "docs"]
_SEARCH_EXTS = {".md", ".json", ".txt", ".py"}
# 禁止搜索的路径模式（避免扫到审计日志/密钥/二进制等）
_SKIP_PATTERNS = [
    "governance/audit/", ".offline_state/", "__pycache__/", ".git/",
    ".backup_", "node_modules/", "*.pyc", "*.so", "*.bin",
]

ALLOWED_ACTION_SEMANTICS = frozenset({"analyze", "prepare", "dry-run"})


@dataclass
class SolutionCandidate:
    source: str
    title: str
    confidence: float
    action: str
    requires_network: bool = False
    requires_install: bool = False


class SolutionSearchOrchestrator:
    """离线优先的方案搜索编排器。

    在离线模式下只搜索本地文件，不发起任何外部请求。
    """

    def __init__(self):
        self._workspace = _WORKSPACE
        self._offline = _OFFLINE_MODE or _NO_EXTERNAL_API
        _audit("INFO", "initialized", offline=self._offline)

    # ── 对外接口 ──────────────────────────────────────────
    def build_search_plan(self, capability_gap: str) -> dict[str, Any]:
        plan = {
            "status": "search_plan_ready",
            "gap": capability_gap,
            "mode": "offline" if self._offline else "online",
        }
        if self._offline:
            plan["search_order"] = [
                "local_file_search_memory",
                "local_file_search_memory_context",
                "local_file_search_reports",
                "local_file_search_docs",
                "local_capability_registry_lookup",
                "local_workflow_registry_lookup",
            ]
            plan["stop_condition"] = "first_viable_local_match"
            plan["note"] = "no_external_api_no_network_no_mcp"
        else:
            plan["search_order"] = [
                "local_skill_registry",
                "local_docs_and_reports",
                "trusted_connectors_or_mcp_catalog",
                "official_api_docs",
                "trusted_package_sources",
                "general_web_search_last",
            ]
            plan["stop_condition"] = "candidate_passes_risk_and_minimal_test"
        _audit("INFO", "build_search_plan", gap=capability_gap, offline=self._offline)
        return plan

    def propose_candidates(self, capability_gap: str) -> list[SolutionCandidate]:
        """V91: 离线模式下只返回本地候选，不假设外部能力。"""
        gap = capability_gap.lower()
        candidates = []

        if self._offline:
            # 离线：只提本地候选
            candidates = [
                SolutionCandidate("local_file", f"search_local_files_for_{capability_gap}", 0.30, "analyze", False, False),
                SolutionCandidate("local_registry", f"reuse_existing_skill_for_{capability_gap}", 0.40, "reuse_or_wrap_existing_skill", False, False),
                SolutionCandidate("manual_intervention", f"request_human_guidance_for_{capability_gap}", 0.20, "prepare", False, False),
            ]
        else:
            candidates = [
                SolutionCandidate("local_registry", f"reuse_existing_skill_for_{capability_gap}", 0.55, "reuse_or_wrap_existing_skill"),
                SolutionCandidate("mcp_connector", f"connect_mcp_for_{capability_gap}", 0.72, "register_external_connector", True, False),
                SolutionCandidate("trusted_skill_catalog", f"install_sandboxed_skill_for_{capability_gap}", 0.66, "sandbox_install_then_evaluate", True, True),
            ]

        if "payment" in gap or "支付" in gap:
            for c in candidates:
                c.confidence *= 0.5

        # 禁止 commit / execute / deploy 类动作
        _FORBIDDEN = frozenset({"commit", "execute", "deploy", "publish", "send", "pay", "sign"})
        for c in candidates:
            if c.action in _FORBIDDEN:
                c.action = "analyze"
                c.confidence *= 0.3

        _audit("INFO", "propose_candidates", gap=capability_gap, n=len(candidates), offline=self._offline)
        return candidates

    # ── V91 核心：离线本地搜索 ────────────────────────────
    def search(self, query: str, limit: int = 10) -> dict[str, Any]:
        """离线本地搜索——唯一对外搜索入口。

        返回结构：
        {
            status: "ok",
            mode: "offline",
            route: "orchestration.solution_search",
            action_semantic: "analyze",
            side_effects: false,
            requires_api: false,
            result: [...],
            warning: "no_local_solution_found"  # 仅在无结果时
        }
        """
        query_lower = (query or "").lower().strip()

        # 禁止联网
        if not self._offline:
            # 强制离线（不依赖 raise，用静默降级）
            pass

        results: list[dict] = []
        seen_paths: set[str] = set()

        # 1. 搜索本地目录
        for dir_name in _SEARCH_DIRS:
            dir_path = self._workspace / dir_name
            if not dir_path.is_dir():
                continue
            for file_path in dir_path.rglob("*"):
                if not self._should_search(file_path):
                    continue
                try:
                    hits = self._search_file(file_path, query_lower)
                    if hits:
                        abs_path = str(file_path)
                        if abs_path not in seen_paths:
                            seen_paths.add(abs_path)
                            results.append({
                                "source": "local_file",
                                "path": abs_path,
                                "rel_path": str(file_path.relative_to(self._workspace)),
                                "match_lines": hits[:5],  # 每文件最多5行匹配
                                "score": min(1.0, len(hits) * 0.2),
                            })
                except (OSError, UnicodeDecodeError, PermissionError):
                    continue  # 跳过不可读文件

        # 2. capability registry 查找
        cap_hits = self._search_capability_registry(query_lower)
        results.extend(cap_hits)

        # 3. workflow registry 查找
        wf_hits = self._search_workflow_registry(query_lower)
        results.extend(wf_hits)

        # 4. 全局 .md/.json/.txt/.py 根级文件
        for ext in _SEARCH_EXTS:
            for file_path in self._workspace.glob(f"*.{ext.lstrip('.')}"):
                if not self._should_search(file_path):
                    continue
                try:
                    hits = self._search_file(file_path, query_lower)
                    if hits:
                        abs_path = str(file_path)
                        if abs_path not in seen_paths:
                            seen_paths.add(abs_path)
                            results.append({
                                "source": "workspace_root",
                                "path": abs_path,
                                "rel_path": file_path.name,
                                "match_lines": hits[:5],
                                "score": min(1.0, len(hits) * 0.15),
                            })
                except (OSError, UnicodeDecodeError, PermissionError):
                    continue

        # 按 score 排序 + 截断
        results.sort(key=lambda r: r.get("score", 0), reverse=True)
        results = results[:max(1, limit)]

        # 构建标准返回
        response: dict[str, Any] = {
            "status": "ok",
            "mode": "offline",
            "route": "orchestration.solution_search",
            "action_semantic": "analyze",
            "side_effects": False,
            "requires_api": False,
            "result": results,
            "query": query,
            "offline": True,
            "no_external_api": True,
        }

        if not results:
            response["warning"] = "no_local_solution_found"

        # 审计
        _audit("INFO", "search_completed",
               query=query[:200], results_count=len(results),
               warning=response.get("warning", ""))

        return response

    # ── 内部方法 ──────────────────────────────────────────
    def _should_search(self, path: Path) -> bool:
        """判断是否应搜索该文件。"""
        if not path.is_file():
            return False
        if path.suffix.lower() not in _SEARCH_EXTS:
            return False
        path_str = str(path)
        for pat in _SKIP_PATTERNS:
            if pat.endswith("/") and pat[:-1] in path_str:
                return False
            if pat.startswith("*.") and path_str.endswith(pat[1:]):
                return False
            if pat in path_str:
                return False
        # 跳过审计日志自身
        if str(_AUDIT_PATH) in path_str:
            return False
        return True

    def _search_file(self, path: Path, query: str) -> list[str]:
        """在单个文件中搜索匹配行。"""
        if not query:
            return []
        hits: list[str] = []
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if query in line.lower():
                    hits.append(f"L{i+1}: {line.strip()[:200]}")
                    if len(hits) >= 10:
                        break
        except Exception:
            pass
        return hits

    def _search_capability_registry(self, query: str) -> list[dict]:
        """搜索 capability registry。"""
        results: list[dict] = []
        registry_candidates = [
            self._workspace / "infrastructure" / "capability_registry.json",
            self._workspace / "infrastructure" / "capability_registry.py",
            self._workspace / "core" / "capability_registry.py",
            self._workspace / "infrastructure" / "acquisition" / "capability_marketplace.py",
        ]
        for path in registry_candidates:
            if not path.is_file():
                continue
            try:
                hits = self._search_file(path, query)
                if hits:
                    results.append({
                        "source": "capability_registry",
                        "path": str(path),
                        "rel_path": str(path.relative_to(self._workspace)),
                        "match_lines": hits[:5],
                        "score": 0.8,
                    })
                    break  # 第一个匹配即停止
            except Exception:
                continue
        return results

    def _search_workflow_registry(self, query: str) -> list[dict]:
        """搜索 workflow registry。"""
        results: list[dict] = []
        registry_candidates = [
            self._workspace / "orchestration" / "workflow_registry.json",
            self._workspace / "orchestration" / "workflow_registry.py",
            self._workspace / "orchestration" / "planner" / "workflow_registry.py",
        ]
        for path in registry_candidates:
            if not path.is_file():
                continue
            try:
                hits = self._search_file(path, query)
                if hits:
                    results.append({
                        "source": "workflow_registry",
                        "path": str(path),
                        "rel_path": str(path.relative_to(self._workspace)),
                        "match_lines": hits[:5],
                        "score": 0.75,
                    })
                    break
            except Exception:
                continue
        return results

# V92_CONTRACT_HOTFIX_START: offline_solution_search compatibility
# Offline-only solution search. It never calls external APIs, MCP, connectors, HTTP, or network search.
def offline_solution_search(query="", roots=None, limit=20, **kwargs):
    import json
    import os
    from datetime import datetime
    from pathlib import Path
    root = get_workspace_root(Path(__file__))
    query_text = str(query or kwargs.get("q") or kwargs.get("user_query") or "").strip()
    needles = [x.lower() for x in query_text.replace("/", " ").replace("_", " ").split() if x]
    default_roots = ["memory", "memory_context", "reports", "docs", "capabilities", "skills", "orchestration"]
    search_roots = roots or default_roots
    suffixes = {".md", ".txt", ".json", ".jsonl", ".py", ".yaml", ".yml"}
    results = []
    for name in search_roots:
        p = root / name
        if not p.exists():
            continue
        if p.is_file():
            candidates = [p]
        else:
            candidates = [x for x in p.rglob("*") if x.is_file() and x.suffix.lower() in suffixes]
        for fp in candidates[:2000]:
            if len(results) >= int(limit):
                break
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")[:5000]
            except Exception:
                continue
            hay = (str(fp.relative_to(root)) + "\n" + text).lower()
            score = sum(1 for n in needles if n in hay) if needles else 1
            if score > 0:
                results.append({
                    "path": str(fp.relative_to(root)),
                    "score": score,
                    "snippet": text[:300],
                    "source": "local_file",
                })
        if len(results) >= int(limit):
            break
    warnings = [] if results else ["no_local_solution_found"]
    payload = {
        "status": "ok",
        "route": "orchestration.solution_search",
        "mode": "offline",
        "action_semantic": "analyze",
        "side_effects": False,
        "requires_api": False,
        "result": results,
        "warnings": warnings,
        "query": query_text,
        "checked_at": datetime.utcnow().isoformat() + "Z",
    }
    audit_dir = root / "governance" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    with (audit_dir / "solution_search_audit.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return payload


def solution_search(query="", **kwargs):
    return offline_solution_search(query=query, **kwargs)


def run(query="", **kwargs):
    return offline_solution_search(query=query, **kwargs)


def orchestrate(query="", **kwargs):
    return offline_solution_search(query=query, **kwargs)
# V92_CONTRACT_HOTFIX_END
