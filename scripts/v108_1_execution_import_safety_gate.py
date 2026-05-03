#!/usr/bin/env python3
from __future__ import annotations
import os, json, subprocess, sys
from pathlib import Path

ROOT = Path.cwd()
REPORTS = ROOT / 'reports'
REPORTS.mkdir(exist_ok=True)

def write_json(path: Path, payload: dict):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

failures = []
checks = {}
behavior = {}

env = os.environ.copy()
env['PYTHONPATH'] = f"{ROOT}:{env.get('PYTHONPATH','')}"
env.setdefault('OFFLINE_MODE', 'true')
env.setdefault('NO_EXTERNAL_API', 'true')
env.setdefault('DISABLE_LLM_API', 'true')
env.setdefault('DISABLE_THINKING_MODE', 'true')
env.setdefault('NO_REAL_SEND', 'true')
env.setdefault('NO_REAL_PAYMENT', 'true')
env.setdefault('NO_REAL_DEVICE', 'true')
env.setdefault('PYTHONDONTWRITEBYTECODE', '1')

code = """
import execution
print(execution.optional_status())
import execution.unified_tool_execution_gateway as m
print(m.check_tool_call('git push origin main'))
"""
proc = subprocess.run([sys.executable, '-S', '-c', code], cwd=str(ROOT), env=env, capture_output=True, text=True)
checks['execution_package_import_safe'] = proc.returncode == 0
if proc.returncode != 0:
    failures.append('execution_package_import_failed')
behavior['import_stdout'] = proc.stdout[-2000:]
behavior['import_stderr'] = proc.stderr[-2000:]

try:
    import execution
    checks['execution_lazy_facade'] = execution.optional_status().get('lazy_facade') is True
except Exception as e:
    checks['execution_lazy_facade'] = False
    behavior['execution_import_error'] = str(e)
    failures.append('execution_lazy_facade_missing')

try:
    from execution.unified_tool_execution_gateway import check_tool_call
    r = check_tool_call('git push origin main')
    behavior['git_push_check'] = r
    checks['git_push_blocked'] = r.get('status') == 'blocked'
    if r.get('status') != 'blocked':
        failures.append('git_push_not_blocked')
except Exception as e:
    checks['git_push_blocked'] = False
    behavior['tool_gateway_error'] = str(e)
    failures.append('tool_gateway_import_or_behavior_failed')

v108 = subprocess.run([sys.executable, '-S', 'scripts/v108_remaining_unified_systems_gate.py'], cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=120)
checks['v108_gate_no_regression'] = v108.returncode == 0
behavior['v108_stdout_tail'] = v108.stdout[-2000:]
behavior['v108_stderr_tail'] = v108.stderr[-2000:]
if v108.returncode != 0:
    failures.append('v108_gate_regression')

# Read generated V108 report for hard checks.
v108_report = None
p = REPORTS / 'V108_REMAINING_UNIFIED_SYSTEMS_GATE.json'
if p.exists():
    try:
        v108_report = json.loads(p.read_text(encoding='utf-8'))
    except Exception as e:
        v108_report = {'_read_error': str(e)}
checks['v108_report_pass'] = isinstance(v108_report, dict) and v108_report.get('status') == 'pass'
checks['tool_execution_gateway_unified'] = bool(isinstance(v108_report, dict) and v108_report.get('checks', {}).get('tool_execution_gateway_unified'))
if not checks['v108_report_pass']:
    failures.append('v108_report_not_pass')
if not checks['tool_execution_gateway_unified']:
    failures.append('tool_execution_gateway_not_unified')

report = {
    'version': 'V108.1',
    'status': 'pass' if not failures else 'partial',
    'checks': checks,
    'behavior': behavior,
    'v108_report_status': v108_report.get('status') if isinstance(v108_report, dict) else None,
    'remaining_failures': failures,
    'note': 'Fixes execution package eager imports so V108 tool gateway works under python3 -S without pydantic.'
}
write_json(REPORTS / 'V108_1_EXECUTION_IMPORT_SAFETY_GATE.json', report)
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if not failures else 1)
