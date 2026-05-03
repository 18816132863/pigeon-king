#!/usr/bin/env python3
"""V99.1 Operations Dashboard Generator

Produces an HTML dashboard from V97+ gate reports, test results, and system state.
Output: reports/V99_1_OPS_DASHBOARD.html  (standalone, self-contained)
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
REPORTS = ROOT / "reports"
DASHBOARD = REPORTS / "V99_1_OPS_DASHBOARD.html"

# ── Enforce offline env ────────────────────────────────
ENV = {
    "NO_EXTERNAL_API": True,
    "NO_REAL_SEND": True,
    "NO_REAL_PAYMENT": True,
    "NO_REAL_DEVICE": True,
}
for k, v in ENV.items():
    os.environ[k.lower()] = "true"


def now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def file_count(d: Path, ext: str = ".py") -> int:
    return len(list(d.rglob(f"*{ext}"))) if d.exists() else 0


def lines_count(d: Path, ext: str = ".py") -> int:
    total = 0
    for f in d.rglob(f"*{ext}"):
        try:
            total += len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
        except Exception:
            pass
    return total


def gate_history() -> list[dict]:
    gates = []
    for p in sorted(REPORTS.glob("V*GATE.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        d = load_json(p)
        if d:
            gates.append({
                "name": p.stem,
                "status": d.get("status", "?"),
                "remaining": d.get("remaining_failures", []),
                "checked": d.get("checked_at", ""),
            })
    return gates[:30]


def total_gates_passed() -> int:
    return sum(1 for g in gate_history() if g["status"] == "pass")


def layers_stats() -> list[dict]:
    layers = ["core", "memory_context", "orchestration", "execution", "governance", "infrastructure"]
    result = []
    for name in layers:
        p = ROOT / name
        files = file_count(p, ".py")
        lines = lines_count(p, ".py")
        result.append({"name": name, "files": files, "lines": lines})
    return result


def collect_system_metrics() -> dict[str, Any]:
    total_py = sum(l["files"] for l in layers_stats())
    total_lines = sum(l["lines"] for l in layers_stats())
    # Get report sizes
    report_files = len(list(REPORTS.glob("*.json")))
    report_size_mb = round(sum(f.stat().st_size for f in REPORTS.glob("*.json")) / 1024 / 1024, 2)

    # Latest test results
    test_result_path = REPORTS / "V95_2_ALL_CHAIN_COVERAGE_GATE.json"
    chain_data = load_json(test_result_path)

    # V97 stability
    stability = load_json(REPORTS / "V97_LONG_RUN_STABILITY_GATE.json")

    return {
        "layers": layers_stats(),
        "total_py_files": total_py,
        "total_py_lines": total_lines,
        "report_files": report_files,
        "report_size_mb": report_size_mb,
        "gates_passed": total_gates_passed(),
        "gates_total": len(gate_history()),
        "chain_coverage": chain_data.get("chains_passed", "?") if chain_data else "?",
        "chain_total": chain_data.get("chains_total", "?") if chain_data else "?",
        "stability_rounds": stability.get("summary", {}).get("total_runs", "?") if stability else "?",
        "stability_pass": stability.get("summary", {}).get("total_pass", "?") if stability else "?",
    }


# ── HTML Builder ─────────────────────────────────────────
def build_dashboard() -> str:
    metrics = collect_system_metrics()
    gates = gate_history()

    layers_rows = ""
    for l in metrics["layers"]:
        layers_rows += f"""<tr><td>{l['name']}</td><td>{l['files']}</td><td>{l['lines']:,}</td></tr>"""

    gates_rows = ""
    for g in gates:
        icon = "✅" if g["status"] == "pass" else ("⚠️" if g["status"] == "partial" else "❌")
        fails = ", ".join(str(g["remaining"][:5])) if g["remaining"] else "—"
        gates_rows += f"""<tr><td>{g['name']}</td><td>{icon} {g['status']}</td><td style="font-size:0.85em;color:#888">{fails}</td></tr>"""

    html = f"""<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>系统运营仪表盘</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}}
body{{background:#0d1117;color:#c9d1d9;padding:20px;max-width:1200px;margin:0 auto}}
h1{{font-size:1.5rem;margin-bottom:4px;color:#58a6ff}}
.subtitle{{color:#8b949e;font-size:0.9rem;margin-bottom:20px}}
.card-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:24px}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px}}
.card .label{{font-size:0.8rem;color:#8b949e;text-transform:uppercase;letter-spacing:0.5px}}
.card .value{{font-size:1.6rem;font-weight:600;margin-top:4px}}
.card .value.green{{color:#3fb950}}
.card .value.yellow{{color:#d29922}}
.card .value.blue{{color:#58a6ff}}
.card .value.red{{color:#f85149}}
.section-title{{font-size:1.1rem;font-weight:600;margin:20px 0 10px;color:#f0f6fc;border-bottom:1px solid #30363d;padding-bottom:6px}}
table{{width:100%;border-collapse:collapse;margin-bottom:20px}}
th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid #21262d;font-size:0.9rem}}
th{{color:#8b949e;font-weight:500;font-size:0.8rem;text-transform:uppercase}}
tr:hover{{background:#1c2128}}
.pulse{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}}
.pulse.green{{background:#3fb950;box-shadow:0 0 6px #3fb950}}
.pulse.yellow{{background:#d29922;box-shadow:0 0 6px #d29922}}
.pulse.red{{background:#f85149;box-shadow:0 0 6px #f85149}}
.footer{{color:#484f58;font-size:0.8rem;text-align:center;margin-top:40px;padding-top:20px;border-top:1px solid #21262d}}
</style></head><body>

<h1>🖥 系统运营仪表盘</h1>
<p class="subtitle">更新于 {now()} · 全离线运行 · 无外部 API 调用</p>

<div class="card-grid">
<div class="card"><div class="label">总架构层数</div><div class="value blue">6</div></div>
<div class="card"><div class="label">Python 文件</div><div class="value green">{metrics['total_py_files']}</div></div>
<div class="card"><div class="label">代码行数</div><div class="value green">{metrics['total_py_lines']:,}</div></div>
<div class="card"><div class="label">门通过率</div><div class="value green">{metrics['gates_passed']}/{metrics['gates_total']}</div></div>
<div class="card"><div class="label">全链覆盖</div><div class="value yellow">{metrics['chain_coverage']}/{metrics['chain_total']}</div></div>
<div class="card"><div class="label">稳定性轮次</div><div class="value green">{metrics['stability_pass']}/{metrics['stability_rounds']}</div></div>
<div class="card"><div class="label">报告文件</div><div class="value blue">{metrics['report_files']}</div></div>
<div class="card"><div class="label">报告大小</div><div class="value blue">{metrics['report_size_mb']} MB</div></div>
</div>

<div class="section-title">📂 六层架构</div>
<table><thead><tr><th>层级</th><th>文件数</th><th>代码行数</th></tr></thead>
<tbody>{layers_rows}</tbody></table>

<div class="section-title">✅ 门状态历史（最近30条）</div>
<table><thead><tr><th>门</th><th>状态</th><th>剩余失败</th></tr></thead>
<tbody>{gates_rows}</tbody></table>

<div class="section-title">🔐 在线护栏</div>
<div class="card-grid">
<div class="card"><div class="label">外部 API</div><div class="value green">关闭</div></div>
<div class="card"><div class="label">真实支付</div><div class="value green">关闭</div></div>
<div class="card"><div class="label">真实发送</div><div class="value green">关闭</div></div>
<div class="card"><div class="label">真实设备</div><div class="value green">关闭</div></div>
</div>

<div class="footer">V99.1 运营仪表盘 · 由本地数据生成 · 无外部依赖 · 报告路径: {REPORTS}/V99_1_OPS_DASHBOARD.html</div>
</body></html>"""
    return html


def main() -> int:
    html = build_dashboard()
    DASHBOARD.write_text(html, encoding="utf-8")
    print(f"Dashboard generated: {DASHBOARD}")
    print(f"File size: {DASHBOARD.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
