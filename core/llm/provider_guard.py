#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V85 provider guard - final noskills version.

Goal:
  Business modules must not bypass core.llm.call()/LLMGateway.

Default blocking scope:
  core/ except core/llm/
  agent_kernel/
  orchestration/
  execution/
  safety_governor/

Audit-only scope:
  scripts/
  infrastructure/
  skills/  (if present)

Strict mode:
  V85_STRICT_PROVIDER_GUARD=1 scans all Python runtime directories except core/llm and tests.

This version is intentionally bounded to avoid full-workspace scan stalls.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from infrastructure.common.path_utils import get_workspace_root
from typing import Dict, List, Tuple

ROOT = get_workspace_root(Path(__file__))

SKIP_DIR_NAMES = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".venv", "venv", "env", "node_modules", "dist", "build", "site-packages",
}

ALLOW_PREFIXES = (
    "core/llm/",
    "tests/",
)

DEFAULT_BLOCKING_PREFIXES = (
    "core/",
    "agent_kernel/",
    "orchestration/",
    "execution/",
    "safety_governor/",
)

DEFAULT_AUDIT_PREFIXES = (
    "scripts/",
    "infrastructure/",
    "skills/",
)

DIRECT_PATTERNS: Dict[str, re.Pattern] = {
    "provider_sdk_import": re.compile(
        r"^\s*(import|from)\s+("
        r"openai|anthropic|google\.generativeai|dashscope|zhipuai|moonshot|"
        r"mistralai|cohere|groq|ollama|volcenginesdk"
        r")\b",
        re.I | re.M,
    ),
    "direct_chat_completion": re.compile(
        r"(\.chat\.completions\.create\s*\(|\.responses\.create\s*\(|\.messages\.create\s*\(|Generation\.call\s*\(|generate_content\s*\()",
        re.I,
    ),
    "direct_provider_http": re.compile(
        r"(api\.openai\.com|api\.anthropic\.com|generativelanguage\.googleapis|api\.deepseek\.com|dashscope\.aliyuncs\.com|api\.moonshot\.cn|open\.bigmodel\.cn)",
        re.I,
    ),
}

Finding = Tuple[str, str, int, str]


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _has_skip_part(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def _is_allowed(rel: str) -> bool:
    return rel.startswith(ALLOW_PREFIXES)


def _is_blocking_scope(rel: str) -> bool:
    return rel.startswith(DEFAULT_BLOCKING_PREFIXES) and not _is_allowed(rel)


def _is_audit_scope(rel: str) -> bool:
    return rel.startswith(DEFAULT_AUDIT_PREFIXES) and not _is_allowed(rel)


def _candidate_roots(strict: bool) -> List[Path]:
    if strict:
        names = ["core", "agent_kernel", "orchestration", "execution", "safety_governor", "scripts", "infrastructure", "skills"]
    else:
        names = ["core", "agent_kernel", "orchestration", "execution", "safety_governor", "scripts", "infrastructure"]
    return [ROOT / name for name in names if (ROOT / name).exists()]


def _collect_findings() -> List[Finding]:
    strict = os.environ.get("V85_STRICT_PROVIDER_GUARD") == "1"
    findings: List[Finding] = []

    for base in _candidate_roots(strict):
        for path in base.rglob("*.py"):
            if _has_skip_part(path):
                continue
            rel = _rel(path)
            if _is_allowed(rel):
                continue
            if not strict and not (_is_blocking_scope(rel) or _is_audit_scope(rel)):
                continue
            try:
                # Avoid pathological scan cost on generated or vendored giant files.
                if path.stat().st_size > 512_000:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            split = text.splitlines()
            for name, pat in DIRECT_PATTERNS.items():
                for m in pat.finditer(text):
                    line_no = text.count("\n", 0, m.start()) + 1
                    line = split[line_no - 1].strip()[:220] if split else ""
                    findings.append((rel, name, line_no, line))

    return findings


def scan(blocking_only: bool = True) -> List[Finding]:
    strict = os.environ.get("V85_STRICT_PROVIDER_GUARD") == "1"
    findings = _collect_findings()

    if strict or not blocking_only:
        return findings

    return [f for f in findings if _is_blocking_scope(f[0])]


def write_report(findings: List[Finding] | None = None, report_path: Path | None = None) -> Path:
    strict = os.environ.get("V85_STRICT_PROVIDER_GUARD") == "1"
    all_findings = _collect_findings()
    blocking = all_findings if strict else [f for f in all_findings if _is_blocking_scope(f[0])]
    audit_only = [] if strict else [f for f in all_findings if _is_audit_scope(f[0])]

    report_path = report_path or (ROOT / "V85_MODEL_PROVIDER_GUARD_REPORT.txt")
    lines = [
        "V85 MODEL PROVIDER GUARD REPORT",
        "=" * 60,
        f"Root: {ROOT}",
        f"Mode: {'STRICT' if strict else 'DEFAULT_BOUNDED'}",
        f"Blocking findings: {len(blocking)}",
        f"Audit-only findings: {len(audit_only)}",
        "",
    ]

    if blocking:
        lines.append("FAIL: Blocking direct model/API calls found outside core.llm gateway.")
        lines.append("")
        for i, (rel, name, line_no, line) in enumerate(blocking, 1):
            lines.append(f"{i}. {rel}")
            lines.append(f"   type: {name}")
            lines.append(f"   line: {line_no}")
            lines.append(f"   code: {line}")
            lines.append("")
    else:
        lines.append("PASS: No blocking direct provider SDK/API calls outside core.llm gateway.")

    if audit_only:
        lines.append("")
        lines.append("AUDIT-ONLY: Review these before production hardening.")
        lines.append("")
        for i, (rel, name, line_no, line) in enumerate(audit_only, 1):
            lines.append(f"{i}. {rel}")
            lines.append(f"   type: {name}")
            lines.append(f"   line: {line_no}")
            lines.append(f"   code: {line}")
            lines.append("")

    lines.append("")
    lines.append("Required rewrite for blocking business code:")
    lines.append("  from core.llm import call")
    lines.append("  result = call(messages=[{'role': 'user', 'content': prompt}], query=prompt)")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def assert_no_direct_provider_calls() -> None:
    findings = scan(blocking_only=True)
    report = write_report(findings)
    if findings:
        raise SystemExit(f"FAIL: direct provider calls found. See {report}")


if __name__ == "__main__":
    assert_no_direct_provider_calls()
