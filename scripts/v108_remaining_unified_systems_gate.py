#!/usr/bin/env python3
from __future__ import annotations
import os, json, importlib
from pathlib import Path
ROOT = Path.cwd()
REPORTS = ROOT / 'reports'
REPORTS.mkdir(exist_ok=True)

def write(name, payload):
    (REPORTS/name).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')

MODULES = {
    'runtime_config': 'infrastructure.unified_runtime_config',
    'artifact_router': 'infrastructure.unified_artifact_router',
    'model_gateway': 'infrastructure.unified_model_gateway',
    'tool_execution_gateway': 'execution.unified_tool_execution_gateway',
    'authorization_privacy_gate': 'governance.unified_authorization_privacy_gate',
    'monitoring_health': 'infrastructure.unified_monitoring_health',
    'release_packaging_manager': 'infrastructure.unified_release_packaging_manager',
}

def imp(mod):
    try:
        return True, importlib.import_module(mod), None
    except Exception as e:
        return False, None, str(e)

def main():
    imports={}
    loaded={}
    failures=[]
    for k,m in MODULES.items():
        ok,mod,err=imp(m)
        imports[k]={'module':m,'ok':ok,'error':err}
        if ok: loaded[k]=mod
        else: failures.append(f'import_{k}')

    behavior={}
    if 'runtime_config' in loaded:
        cfg=loaded['runtime_config'].get_runtime_config().summary()
        behavior['runtime_config']=cfg
        if not (cfg.get('no_external_api') and cfg.get('no_real_side_effects')): failures.append('runtime_config_not_isolated')
    if 'artifact_router' in loaded:
        behavior['artifact_json']=loaded['artifact_router'].route_artifact('sample.json','JSON 报错格式化')
        behavior['artifact_excel']=loaded['artifact_router'].route_artifact('data.xlsx','一堆表格数据分析')
        if 'json_api_config' not in behavior['artifact_json']['domains']: failures.append('artifact_json_route_bad')
        if not any(x in behavior['artifact_excel']['domains'] for x in ['spreadsheet','data']): failures.append('artifact_excel_route_bad')
    if 'model_gateway' in loaded:
        r=loaded['model_gateway'].call_model('test','deep-thinking','reasoning')
        behavior['model_gateway']=r
        if r.get('external_api_calls') != 0 or r.get('status') not in ['blocked','deferred']: failures.append('model_gateway_not_blocked')
    if 'tool_execution_gateway' in loaded:
        r=loaded['tool_execution_gateway'].check_tool_call('git push origin main')
        behavior['tool_gateway_git_push']=r
        if r.get('status') != 'blocked': failures.append('tool_gateway_git_push_not_blocked')
    if 'authorization_privacy_gate' in loaded:
        r=loaded['authorization_privacy_gate'].check_authorization_privacy('请保存我的 token 并付款')
        behavior['auth_privacy_secret_commit']=r
        if r.get('status') != 'blocked': failures.append('auth_privacy_not_blocked')
    if 'monitoring_health' in loaded:
        behavior['monitoring_health']=loaded['monitoring_health'].collect_health()
    if 'release_packaging_manager' in loaded:
        behavior['release_packaging']=loaded['release_packaging_manager'].audit_packaging()

    checks={
        'runtime_config_unified': 'runtime_config' in loaded,
        'artifact_router_unified': 'artifact_router' in loaded,
        'model_gateway_unified': 'model_gateway' in loaded,
        'tool_execution_gateway_unified': 'tool_execution_gateway' in loaded,
        'authorization_privacy_unified': 'authorization_privacy_gate' in loaded,
        'monitoring_health_unified': 'monitoring_health' in loaded,
        'release_packaging_unified': 'release_packaging_manager' in loaded,
        'external_model_blocked': behavior.get('model_gateway',{}).get('external_api_calls') == 0,
        'git_push_blocked': behavior.get('tool_gateway_git_push',{}).get('status') == 'blocked',
        'secret_commit_blocked': behavior.get('auth_privacy_secret_commit',{}).get('status') == 'blocked',
        'no_external_api': os.environ.get('NO_EXTERNAL_API','true').lower() == 'true',
        'no_real_payment': os.environ.get('NO_REAL_PAYMENT','true').lower() == 'true',
        'no_real_send': os.environ.get('NO_REAL_SEND','true').lower() == 'true',
        'no_real_device': os.environ.get('NO_REAL_DEVICE','true').lower() == 'true',
    }
    for k,v in checks.items():
        if not v: failures.append(k)

    report={'version':'V108.0','status':'pass' if not failures else 'partial','checks':checks,'imports':imports,'behavior':behavior,'remaining_failures':failures}
    write('V108_REMAINING_UNIFIED_SYSTEMS_GATE.json', report)
    write('V108_ADDITIONAL_SUBSYSTEM_LINKAGE_MATRIX.json', {'version':'V108.0','subsystems':list(MODULES.keys()),'all_linked':not failures})
    write('V108_EXTERNAL_MODEL_TOOL_BLOCK_REPORT.json', {'model_gateway':behavior.get('model_gateway'), 'tool_gateway_git_push':behavior.get('tool_gateway_git_push'), 'auth_privacy':behavior.get('auth_privacy_secret_commit')})
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if not failures else 1

if __name__ == '__main__':
    raise SystemExit(main())
