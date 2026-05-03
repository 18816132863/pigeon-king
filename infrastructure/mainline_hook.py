from __future__ import annotations
from pathlib import Path
import json, os, time
ROOT=Path(__file__).resolve().parents[1]; STATE=ROOT/'.v98_state'; STATE.mkdir(exist_ok=True); _last_goal=None
def set_last_goal(goal):
    global _last_goal; _last_goal=goal; return {'status':'ok','last_goal':goal}
def run(message=None, goal=None, mode='pre_reply'):
    if goal: set_last_goal(goal)
    try:
        from memory_context.unified_continuity_engine import bootstrap_for_reply
        from infrastructure.context_loading_engine import UnifiedContextLoadingEngine
        from governance.skill_intelligence_engine import recommend_skills
        loader=UnifiedContextLoadingEngine(); p0=loader.preload_p0(); p1=loader.warm_p1(); continuity=bootstrap_for_reply(message or goal or '', {'mode':mode}); skills=recommend_skills(message or goal or '', {'mode':mode}, top_k=5) if (message or goal) else []
    except Exception as e:
        p0=[]; p1=[]; continuity={'status':'warning','error':str(e)}; skills=[]
    payload={'status':'ok','mode':mode,'context_summary':continuity,'guardrail_summary':{'offline':os.environ.get('OFFLINE_MODE')=='true','no_external_api':os.environ.get('NO_EXTERNAL_API')=='true','no_real_payment':os.environ.get('NO_REAL_PAYMENT')=='true','no_real_send':os.environ.get('NO_REAL_SEND')=='true','no_real_device':os.environ.get('NO_REAL_DEVICE')=='true'},'capability_truth_summary':{'implemented':['V90/V92/V100 gate','V95.2 chain coverage','V96 failure recovery','V107 unified bus'],'simulated':['embodied perception','emotion tags','continuous presence via context reload'],'planned':['real body','real sensor','live credential'],'forbidden':['real payment','real send','real device','real signature']},'runtime_fusion_summary':{'p0_preloaded':len(p0),'p1_warmed':len(p1),'skill_recommendations':len(skills)},'proactive_skill_summary':skills[:3],'heavy_chain_triggered':False,'persona_mode':True,'persona_does_not_override_governance':True,'fail_soft':True,'last_goal':goal or _last_goal,'ts':time.time()}
    with (STATE/'mainline_hook_heartbeat.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(payload,ensure_ascii=False)+'\n')
    return payload
def pre_reply(message=None, goal=None): return run(message=message, goal=goal, mode='pre_reply')
