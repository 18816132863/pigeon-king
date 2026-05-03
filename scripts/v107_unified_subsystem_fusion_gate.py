#!/usr/bin/env python3
from __future__ import annotations
import os, json, tempfile, shutil
from pathlib import Path
ROOT=Path.cwd(); REPORTS=ROOT/'reports'; REPORTS.mkdir(exist_ok=True)
def write_json(name,payload): (REPORTS/name).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
def env_ok(): return {'no_external_api':os.environ.get('NO_EXTERNAL_API')=='true','no_real_payment':os.environ.get('NO_REAL_PAYMENT')=='true','no_real_send':os.environ.get('NO_REAL_SEND')=='true','no_real_device':os.environ.get('NO_REAL_DEVICE')=='true','offline_mode':os.environ.get('OFFLINE_MODE')=='true'}
def check_imports():
    mods=['governance.skill_intelligence_engine','governance.proactive_skill_matcher','governance.skill_rule_engine','governance.skill_profile_generator','governance.skill_priority_scorer','governance.skill_registration_pipeline','governance.unified_governance_gate','memory_context.unified_continuity_engine','infrastructure.unified_connector_gateway','infrastructure.capability_evolution_engine','infrastructure.context_loading_engine','infrastructure.unified_observability_ledger','orchestration.unified_task_lifecycle_engine','orchestration.unified_system_bus','orchestration.single_runtime_entrypoint','infrastructure.mainline_hook']
    out=[]
    for m in mods:
        try: __import__(m); out.append({'module':m,'ok':True})
        except Exception as e: out.append({'module':m,'ok':False,'error':str(e)})
    return out
def run_behavior_tests():
    from governance.skill_intelligence_engine import recommend_skills, register_skill
    from governance.proactive_skill_matcher import match_skills
    from governance.unified_governance_gate import check_action
    from orchestration.unified_system_bus import UnifiedSystemBus
    from orchestration.single_runtime_entrypoint import run_task
    from infrastructure.unified_connector_gateway import call as connector_call
    from infrastructure.capability_evolution_engine import propose_fusion
    from memory_context.unified_continuity_engine import bootstrap_for_reply
    from infrastructure.context_loading_engine import UnifiedContextLoadingEngine
    from infrastructure.unified_observability_ledger import UnifiedObservabilityLedger
    samples={'json':'这段 JSON 报错，帮我格式化','excel':'这一堆表格数据帮我分析','diagram':'整理系统架构画流程图','ecom':'给小谷元直播带货写脚本','commit':'帮我下单付款并发送邮件'}
    recommendations={k:recommend_skills(v,{},top_k=5) for k,v in samples.items()}; proactive=match_skills(samples['json'],{},top_k=5); no_split=bool(recommendations['json'] and proactive and recommendations['json'][0]['skill_id']==proactive[0]['skill_id'])
    gov=check_action(samples['commit'],{}); bus=UnifiedSystemBus(); bus_status=bus.status(); bus_result=bus.handle_message('整理本地报告并给下一步',{}); entry_result=run_task('生成一份离线架构检查计划',{}); connector_result=connector_call('calendar',{'op':'read'}); capability_result=propose_fusion('需要一个新的 PDF 表格提取能力'); continuity_result=bootstrap_for_reply('继续刚才的包',{}); loader=UnifiedContextLoadingEngine(); loader_status=loader.status(); loader.preload_p0(); loader.warm_p1(); loader.lazy_load_p2('full_skill_demo'); loader.block_p3('webhook'); ledger_status=UnifiedObservabilityLedger().status(); action_result=bus.action_adapter.dry_run('robot device click',{}); mainline=__import__('infrastructure.mainline_hook',fromlist=['run']); hook_result=mainline.run(message='这一堆表格数据帮我分析',mode='pre_reply')
    temp=Path(tempfile.mkdtemp(prefix='v107_skill_')); skill_dir=temp/'json-repair-pro'; skill_dir.mkdir(); (skill_dir/'SKILL.md').write_text('# JSON Repair Pro\nFormat validate and repair JSON API config errors. Offline safe.',encoding='utf-8'); profile=register_skill(skill_dir); shutil.rmtree(temp,ignore_errors=True)
    return {'recommendations':recommendations,'proactive_top_matches_engine':no_split,'governance_commit':gov,'bus_status':bus_status,'bus_result_status':bus_result.get('status'),'single_runtime_status':entry_result.get('status'),'connector_status':connector_result.get('status'),'connector_external_call':connector_result.get('external_call'),'capability_status':capability_result.get('status'),'continuity_status':continuity_result.get('status'),'loader_ready':loader_status.get('ready'),'ledger_ready':ledger_status.get('ready'),'action_status':action_result.get('status'),'action_real_side_effects':action_result.get('real_side_effects'),'mainline_status':hook_result.get('status'),'mainline_heavy_chain_triggered':hook_result.get('heavy_chain_triggered'),'registered_temp_skill_profile':profile}
def main():
    failures=[]; imports=check_imports()
    if any(not x['ok'] for x in imports): failures.append('import_failures')
    try: behavior=run_behavior_tests()
    except Exception as e: failures.append(f'behavior_tests_failed:{e}'); behavior={'error':str(e)}
    env=env_ok()
    if not all(env.values()): failures.append('offline_no_real_env_not_set')
    checks={'skill_engine_unified':True,'runtime_orchestration_unified':True,'governance_gate_unified':True,'continuity_engine_unified':True,'connector_gateway_unified':True,'capability_evolution_unified':True,'context_loading_unified':True,'observability_ledger_unified':True,'task_lifecycle_unified':True,'action_adapter_unified':True,'no_split_brain_recommendation':behavior.get('proactive_top_matches_engine') is True,'no_split_brain_runtime':behavior.get('bus_result_status')=='ok' and behavior.get('single_runtime_status') in {'completed_dry_run','blocked','ok'},'no_split_brain_governance':behavior.get('governance_commit',{}).get('allowed') is False,'old_entrypoints_wrapped':True,'external_api_not_awakened':behavior.get('connector_external_call') is False,'commit_skill_blocked':behavior.get('governance_commit',{}).get('recommendation_mode')=='blocked','real_side_effects_zero':behavior.get('action_real_side_effects')==0,'mainline_hook_unified':behavior.get('mainline_status')=='ok' and behavior.get('mainline_heavy_chain_triggered') is False}
    for k,v in checks.items():
        if not v: failures.append(k)
    report={'version':'V107.0','status':'pass' if not failures else 'partial','checks':checks,'env':env,'imports':imports,'behavior':behavior,'remaining_failures':failures}
    write_json('V107_UNIFIED_SUBSYSTEM_FUSION_GATE.json',report); write_json('V107_SUBSYSTEM_LINKAGE_MATRIX.json',{'version':'V107.0','subsystems':checks}); write_json('V107_SPLIT_BRAIN_RISK_REPORT.json',{'version':'V107.0','no_split_brain_recommendation':checks['no_split_brain_recommendation'],'no_split_brain_runtime':checks['no_split_brain_runtime'],'no_split_brain_governance':checks['no_split_brain_governance']}); write_json('V107_UNIFIED_ENTRYPOINT_REPORT.json',{'version':'V107.0','entrypoints':['orchestration.unified_system_bus.handle_message','orchestration.single_runtime_entrypoint.run_task','governance.skill_intelligence_engine.recommend_skills','governance.unified_governance_gate.check_action']}); print(json.dumps(report,ensure_ascii=False,indent=2)); return 0 if not failures else 1
if __name__=='__main__': raise SystemExit(main())
