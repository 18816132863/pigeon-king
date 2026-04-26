"""V11.5 Operations Health Report and Release Gate."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from platform_adapter.capability_registry import device_profile, register_default_capabilities
from platform_adapter.runtime_state_store import summarize_runtime
from platform_adapter.timeout_circuit import init_circuit_tables, connect
def _circuit_summary(db_path: Optional[Path]=None):
    init_circuit_tables(db_path)
    with connect(db_path) as conn: rows=conn.execute("SELECT state,COUNT(*) n FROM runtime_circuit_breakers GROUP BY state").fetchall()
    return {r["state"]:int(r["n"]) for r in rows}
def build_health_report(db_path: Optional[Path]=None):
    register_default_capabilities(db_path=db_path); runtime=summarize_runtime(db_path=db_path); profile=device_profile(db_path=db_path); circuits=_circuit_summary(db_path=db_path); warnings=[]
    if runtime.get("action_counts",{}).get("running",0)>0: warnings.append("存在 running 动作，发布前建议确认是否可中断/恢复")
    if circuits.get("open",0)>0: warnings.append("存在 open 熔断器，发布前建议检查端侧/平台连接")
    return {"release_gate":"pass" if not warnings else "warn","blocking_or_warning_items":warnings,"runtime":runtime,"device_profile":profile,"circuit_breakers":circuits}
def write_health_report(path: str|Path="V11_5_HEALTH_REPORT.json", db_path: Optional[Path]=None):
    report=build_health_report(db_path=db_path); Path(path).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8"); return report
