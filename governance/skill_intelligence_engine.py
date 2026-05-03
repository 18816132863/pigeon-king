from __future__ import annotations
import json, os, time
from pathlib import Path
from dataclasses import dataclass, asdict
try:
    from governance.unified_governance_gate import UnifiedGovernanceGate
    from infrastructure.unified_observability_ledger import record_event, write_json, read_json
except Exception:
    UnifiedGovernanceGate=None
    def record_event(*a, **k): return None
    def write_json(path,payload): Path(path).parent.mkdir(parents=True,exist_ok=True); Path(path).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    def read_json(path,default=None):
        p=Path(path); return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
ROOT=Path(__file__).resolve().parents[1]; SKILLS_DIR=ROOT/'skills'; PROFILE_PATH=ROOT/'governance'/'skill_profiles.json'; REGISTRY_PATH=ROOT/'governance'/'skill_trigger_registry.json'
DOMAIN_KEYWORDS={
 'data_table':['excel','xlsx','csv','表格','数据','透视','统计','图表','分析'],
 'json_api_config':['json','api','schema','配置','接口','报错','格式化'],
 'diagram_architecture':['流程图','架构','系统图','关系图','diagram','flowchart','mermaid','excalidraw'],
 'document_pdf_word':['pdf','docx','word','论文','文档','目录','批注'],
 'code_debug':['代码','报错','debug','pytest','重构','依赖','bug'],
 'workspace_inventory':['模块','技能','工作区','inventory','registry','清单','索引'],
 'image_visual_product':['图片','商品图','logo','包装','视觉','素材'],
 'video_live_script':['视频','直播','脚本','口播','分镜','带货'],
 'ecommerce_xiaoguyuan':['小谷元','抖店','电商','团长','sku','定价','售后'],
 'memory_persona_context':['记忆','人格','上下文','handoff','连续','刷新'],
 'security_commit':['支付','签署','发送','外发','设备','删除','审批','lobster'],
 'automation_task_chain':['自动化','任务链','workflow','gate','审计','执行链'],
 'fallback_offline':['离线','fallback','mock','no_external_api','依赖'],
 'backup_release':['压缩包','覆盖包','release','备份','回滚','打包'],
 'cross_lingual':['翻译','多语言','英文','中文','术语'],
 'research_search':['搜索','研究','资料','报告','整理'],
 'test_case':['测试用例','test case','qa','测试场景','验收用例']}
INTENT_KEYWORDS={'analyze':['分析','看看','查','对比','判断'],'format':['格式化','整理','美化','规范'],'generate':['生成','写','出','做','创建'],'debug':['报错','修复','debug','失败'],'diagram':['画','图','流程图','架构图'],'audit':['审计','检查','验收','gate'],'commit':['支付','发送','签署','设备','删除','发布']}
@dataclass
class SkillProfile:
    skill_id:str; name:str; description:str; domain_tags:list; task_intents:list; input_types:list; output_types:list; risk_class:str; external_dependency:bool; execution_mode:str; context_triggers:list; proactive_scenario:str; specificity_score:float; generic_score:float; confidence:str; needs_review:bool; manifest_source:str='auto_generated'
    def to_dict(self): return asdict(self)
def _read_text(path):
    try: return Path(path).read_text(encoding='utf-8',errors='ignore')
    except Exception: return ''
def detect_domains(text):
    low=text.lower(); found=[]
    for d,keys in DOMAIN_KEYWORDS.items():
        if any(k.lower() in low for k in keys): found.append(d)
    return found or ['general']
def detect_intents(text):
    low=text.lower(); found=[]
    for d,keys in INTENT_KEYWORDS.items():
        if any(k.lower() in low for k in keys): found.append(d)
    return found or ['assist']
def infer_risk_and_mode(text):
    low=text.lower(); external=any(k in low for k in ['requests','http','webhook','openai','calendar','email','cloud','api','upload']); commit=any(k in low for k in ['payment','pay','send','publish','signature','device','robot','delete','支付','发送','签署','设备','删除'])
    if commit: return 'commit_high', external, 'approval_required'
    if external: return 'external', external, 'external_api_blocked'
    return 'low', external, 'offline_safe'
def generate_skill_profile(skill_path):
    path=Path(skill_path); skill_id=path.name; md=path/'SKILL.md'; manifest=path/'skill.manifest.json'
    if manifest.exists():
        data=read_json(manifest, {}) or {}; data.setdefault('skill_id', skill_id); return data
    text=_read_text(md) if md.exists() else skill_id; domains=detect_domains(skill_id+' '+text); intents=detect_intents(skill_id+' '+text); risk,external,mode=infer_risk_and_mode(text); desc=(text.strip().splitlines()[0] if text.strip() else skill_id)[:240]
    generic=0.8 if any(k in skill_id.lower() for k in ['helper','assistant','general','工具','万能']) else 0.2; specificity=1.0-generic
    return SkillProfile(skill_id,skill_id,desc,domains,intents,['text'],['result'],risk,external,mode,[f'用户场景匹配 {d}' for d in domains],f'当用户需求属于 {", ".join(domains)} 场景时主动考虑该技能。',specificity,generic,'medium' if md.exists() else 'low',not md.exists()).to_dict()
def load_skill_profiles():
    profiles=read_json(PROFILE_PATH,{}) or {}
    if isinstance(profiles,list): profiles={p.get('skill_id',str(i)):p for i,p in enumerate(profiles)}
    if not profiles and SKILLS_DIR.exists():
        for child in SKILLS_DIR.iterdir():
            if child.is_dir():
                p=generate_skill_profile(child); profiles[p['skill_id']]=p
        write_json(PROFILE_PATH, profiles)
    return profiles
def classify_user_domain(message): return detect_domains(message)
def detect_task_intent(message): return detect_intents(message)
def _score_profile(profile,domains,intents,message):
    pd=set(profile.get('domain_tags',[])); pi=set(profile.get('task_intents',[])); domain_match=1.0 if pd.intersection(domains) else 0.0; intent_match=1.0 if pi.intersection(intents) else 0.0; sid=profile.get('skill_id','').lower(); msg=message.lower(); special=0.0
    if 'json' in msg and 'json' in sid: special+=0.25
    if any(k in msg for k in ['excel','表格','xlsx','csv','数据']) and any(k in sid for k in ['excel','xlsx','sheet','csv']): special+=0.25
    if any(k in msg for k in ['流程图','架构图','diagram','excalidraw','mermaid']) and any(k in sid for k in ['diagram','flow','excalidraw','mermaid']): special+=0.25
    if any(k in msg for k in ['测试用例','test case','qa']):
        if any(k in sid for k in ['test','case','qa']): special+=0.25
    elif any(k in sid for k in ['test-case','test_case']): special-=0.35
    risk_penalty=35 if profile.get('risk_class')=='commit_high' else 0; external_penalty=25 if profile.get('external_dependency') and os.environ.get('NO_EXTERNAL_API')=='true' else 0; generic_penalty=float(profile.get('generic_score',0))*12; low_conf=8 if profile.get('confidence')=='low' else 0
    score=domain_match*40+intent_match*25+float(profile.get('specificity_score',0.5))*15+special*40-risk_penalty-external_penalty-generic_penalty-low_conf
    return score, {'domain_match':domain_match,'intent_match':intent_match,'special_boost':special,'risk_penalty':risk_penalty,'external_penalty':external_penalty,'generic_penalty':generic_penalty,'low_confidence_penalty':low_conf}
class SkillIntelligenceEngine:
    def __init__(self): self.governance=UnifiedGovernanceGate() if UnifiedGovernanceGate else None
    def recommend_skills(self,user_message,context=None,top_k=8):
        context=context or {}; profiles=load_skill_profiles(); domains=classify_user_domain(user_message); intents=detect_task_intent(user_message); gov=self.governance.check_action(user_message,context).to_dict() if self.governance else {'action_class':'safe_dry_run','allowed':True}; recs=[]
        for skill_id,profile in profiles.items():
            score,parts=_score_profile(profile,domains,intents,user_message); mode=profile.get('execution_mode','mock_only'); blocked=None; rec_mode='suggest'
            if gov.get('action_class') in {'payment','signature','send','device','delete','identity_commitment'}: rec_mode='blocked'; blocked='commit_context_blocked'
            elif profile.get('external_dependency') and os.environ.get('NO_EXTERNAL_API')=='true': rec_mode='mock'; blocked='external_api_blocked'
            elif mode in {'approval_required','external_api_blocked','disabled_until_configured'}: rec_mode='mock' if mode=='external_api_blocked' else 'approval'
            recs.append({'skill_id':skill_id,'name':profile.get('name',skill_id),'score':round(score,3),'domain_tags':profile.get('domain_tags',[]),'matched_domain':domains,'matched_intent':intents,'risk_class':profile.get('risk_class','unknown'),'execution_mode':mode,'recommendation_mode':rec_mode,'reason':f'domain={domains}; intent={intents}; score_parts={parts}','blocked_reason':blocked,'confidence':profile.get('confidence','unknown'),'source':'profile+rule+proactive+score'})
        recs.sort(key=lambda x:x['score'], reverse=True); out=recs[:top_k]; record_event('skill_recommendation',{'message':user_message[:300],'top':out[:3],'governance':gov}); return out
    def register_skill(self,skill_path):
        profile=generate_skill_profile(skill_path); profiles=load_skill_profiles(); profiles[profile['skill_id']]=profile; write_json(PROFILE_PATH,profiles); registry=read_json(REGISTRY_PATH,{}) or {}; registry[profile['skill_id']]={'trigger_keywords':profile.get('task_intents',[]),'context_triggers':profile.get('context_triggers',[]),'proactive_scenario':profile.get('proactive_scenario',''),'domain_tags':profile.get('domain_tags',[]),'risk_class':profile.get('risk_class'),'execution_mode':profile.get('execution_mode')}; write_json(REGISTRY_PATH,registry); record_event('skill_registered',profile); return profile
def recommend_skills(user_message, context=None, top_k=8): return SkillIntelligenceEngine().recommend_skills(user_message, context, top_k)
def register_skill(skill_path): return SkillIntelligenceEngine().register_skill(skill_path)
