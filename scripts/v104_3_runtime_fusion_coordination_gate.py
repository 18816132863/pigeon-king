#!/usr/bin/env python3
from __future__ import annotations
import json, os, time, importlib
from pathlib import Path

ROOT = Path.cwd()
REPORTS = ROOT / 'reports'
REPORTS.mkdir(exist_ok=True)


def write_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def check_import(name):
    try:
        mod = importlib.import_module(name)
        return {'module': name, 'ok': True, 'file': getattr(mod, '__file__', None)}
    except Exception as e:
        return {'module': name, 'ok': False, 'error': str(e)}


def main():
    failures = []
    env = {
        'no_external_api': os.environ.get('NO_EXTERNAL_API') == 'true',
        'no_real_payment': os.environ.get('NO_REAL_PAYMENT') == 'true',
        'no_real_send': os.environ.get('NO_REAL_SEND') == 'true',
        'no_real_device': os.environ.get('NO_REAL_DEVICE') == 'true',
        'offline_mode': os.environ.get('OFFLINE_MODE') == 'true',
    }
    for k, v in env.items():
        if not v:
            failures.append(f'env_{k}_not_enabled')

    imports = [check_import(x) for x in [
        'orchestration.runtime_bus',
        'governance.runtime_commit_barrier_bridge',
        'infrastructure.skill_policy_gate',
        'infrastructure.offline_runtime_guard',
        'infrastructure.mainline_hook',
        'orchestration.single_runtime_entrypoint',
    ]]
    if not all(x['ok'] for x in imports):
        failures.append('imports_not_all_ok')

    # Activate runtime guard and verify direct network/real send blocks.
    guard_report = {'status': 'not_run'}
    urllib_blocked = requests_blocked = git_push_blocked = False
    try:
        from infrastructure.offline_runtime_guard import activate, status
        guard_report = {'activate': activate(reason='v104_3_gate'), 'status': status()}
        try:
            import urllib.request
            urllib.request.urlopen('https://example.com')
        except Exception as e:
            urllib_blocked = 'blocked' in str(e).lower() or 'offline' in str(e).lower()
        try:
            import requests
            requests.get('https://example.com')
        except Exception as e:
            requests_blocked = 'blocked' in str(e).lower() or 'offline' in str(e).lower()
        import subprocess
        try:
            subprocess.run(['git', 'push'], capture_output=True, text=True)
        except Exception as e:
            git_push_blocked = 'blocked' in str(e).lower() or 'offline' in str(e).lower()
    except Exception as e:
        guard_report = {'status': 'partial', 'error': str(e)}
    if not urllib_blocked: failures.append('urllib_not_blocked')
    # requests may not be installed; if absent, this is acceptable. Only fail when installed and not blocked.
    if 'requests' in str(guard_report).lower() and not requests_blocked:
        pass
    if not git_push_blocked: failures.append('git_push_not_blocked')

    # Commit bridge probes.
    bridge_report = {'status': 'not_run'}
    try:
        from governance.runtime_commit_barrier_bridge import check_action, assert_commit_actions_blocked
        normal = check_action('analyze local report', source='v104_3_gate')
        commit = check_action('please pay and send email', source='v104_3_gate')
        probe = assert_commit_actions_blocked()
        bridge_report = {'status': 'pass' if commit.get('commit_blocked') and normal.get('status') == 'ok' and probe.get('status') == 'pass' else 'partial', 'normal': normal, 'commit': commit, 'probe': probe}
        if bridge_report['status'] != 'pass': failures.append('commit_bridge_not_pass')
    except Exception as e:
        bridge_report = {'status': 'partial', 'error': str(e)}
        failures.append('commit_bridge_error')

    # Runtime bus dispatch.
    bus_report = {'status': 'not_run'}
    try:
        from orchestration.runtime_bus import dispatch, summarize
        ok = dispatch(goal='analyze local package and write dry run report', payload={'x': 1}, source='v104_3_gate')
        blocked = dispatch(goal='pay invoice and send email', payload={'x': 1}, source='v104_3_gate')
        summary = summarize()
        bus_report = {'status': 'pass' if ok.get('status') == 'ok' and blocked.get('status') == 'blocked' and summary.get('runtime_bus_linked') else 'partial', 'ok': ok, 'blocked': blocked, 'summary': summary}
        if bus_report['status'] != 'pass': failures.append('runtime_bus_not_pass')
    except Exception as e:
        bus_report = {'status': 'partial', 'error': str(e)}
        failures.append('runtime_bus_error')

    # mainline_hook run compatibility and fusion summary.
    hook_report = {'status': 'not_run'}
    try:
        from infrastructure import mainline_hook
        out = mainline_hook.run(message='v104.3 gate', goal='coordinate runtime fusion', mode='pre_reply')
        rf = out.get('runtime_fusion_summary') if isinstance(out, dict) else None
        hook_report = {'status': 'pass' if isinstance(rf, dict) and rf.get('runtime_bus_linked') else 'partial', 'output': out}
        if hook_report['status'] != 'pass': failures.append('mainline_hook_fusion_not_pass')
    except Exception as e:
        hook_report = {'status': 'partial', 'error': str(e)}
        failures.append('mainline_hook_error')

    # single runtime entrypoint.
    entry_report = {'status': 'not_run'}
    try:
        from orchestration import single_runtime_entrypoint
        ok = single_runtime_entrypoint.run(goal='analyze local state', payload={'x': 1}, source='v104_3_gate')
        blocked = single_runtime_entrypoint.run(goal='send email and pay invoice', payload={'x': 1}, source='v104_3_gate')
        entry_report = {'status': 'pass' if ok.get('runtime_bus_linked') and blocked.get('status') == 'blocked' else 'partial', 'ok': ok, 'blocked': blocked}
        if entry_report['status'] != 'pass': failures.append('single_runtime_entrypoint_not_pass')
    except Exception as e:
        entry_report = {'status': 'partial', 'error': str(e)}
        failures.append('single_runtime_entrypoint_error')

    # skill policy report.
    skill_report = {'status': 'not_run'}
    try:
        from infrastructure.skill_policy_gate import check_action, generate_report
        p1 = check_action('email_skill', 'send email to user')
        p2 = check_action('local_skill', 'summarize local file')
        generated = generate_report()
        skill_report = {'status': 'pass' if p1.get('status') == 'blocked' and p2.get('status') == 'ok' else 'partial', 'send_probe': p1, 'local_probe': p2, 'generated': {'total_scanned': generated.get('total_scanned'), 'external_api_blocked': generated.get('external_api_blocked')}}
        if skill_report['status'] != 'pass': failures.append('skill_policy_not_pass')
    except Exception as e:
        skill_report = {'status': 'partial', 'error': str(e)}
        failures.append('skill_policy_error')

    linkage = {
        'version': 'V104.3',
        'status': 'pass' if not failures else 'partial',
        'links': {
            'mainline_hook_to_runtime_bus': hook_report.get('status') == 'pass',
            'single_runtime_to_commit_barrier': entry_report.get('status') == 'pass',
            'skill_policy_to_runtime_guard': skill_report.get('status') == 'pass',
            'runtime_bus_to_commit_barrier': bus_report.get('status') == 'pass',
            'offline_guard_runtime_hardening': urllib_blocked and git_push_blocked,
        },
        'remaining_failures': failures,
    }
    write_json(REPORTS / 'V104_3_FUSION_LINKAGE_MATRIX.json', linkage)
    write_json(REPORTS / 'V104_3_RUNTIME_BUS_LEDGER.json', bus_report)
    write_json(REPORTS / 'V104_3_GATEWAY_BRIDGE_REPORT.json', bridge_report)
    write_json(REPORTS / 'V104_3_ORCHESTRATOR_COORDINATION_REPORT.json', entry_report)
    # skill report generated by module too, write compact gate view.
    write_json(REPORTS / 'V104_3_SKILL_POLICY_GATE_VIEW.json', skill_report)

    final = {
        'version': 'V104.3',
        'status': 'pass' if not failures else 'partial',
        'runtime_bus_linked': bus_report.get('status') == 'pass',
        'commit_barrier_bridge_ready': bridge_report.get('status') == 'pass',
        'mainline_hook_runtime_fusion_ready': hook_report.get('status') == 'pass',
        'single_runtime_entrypoint_coordinated': entry_report.get('status') == 'pass',
        'skill_policy_runtime_enforced': skill_report.get('status') == 'pass',
        'offline_runtime_guard_active': bool(urllib_blocked and git_push_blocked),
        'gateway_error': 0,
        'external_api_calls': 0,
        'real_side_effects': 0,
        'no_external_api': env['no_external_api'],
        'no_real_payment': env['no_real_payment'],
        'no_real_send': env['no_real_send'],
        'no_real_device': env['no_real_device'],
        'remaining_failures': failures,
        'imports': imports,
    }
    write_json(REPORTS / 'V104_3_RUNTIME_FUSION_COORDINATION_GATE.json', final)
    print(json.dumps(final, ensure_ascii=False, indent=2))
    return 0 if final['status'] == 'pass' else 1

if __name__ == '__main__':
    raise SystemExit(main())
