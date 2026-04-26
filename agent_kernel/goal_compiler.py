from __future__ import annotations
from dataclasses import dataclass,asdict
from hashlib import sha256
from datetime import datetime,timezone
import re,json
@dataclass
class GoalContract:
    goal_id:str; raw_request:str; objective:str; objective_tree:list; constraints:list; priority:str; time_scope:str; risk_boundary:str; information_sources:list; automatic_parts:list; approval_points:list; done_definition:list; created_at:str
    def to_dict(self): return asdict(self)
    def to_json(self): return json.dumps(self.to_dict(),ensure_ascii=False,indent=2)
class GoalCompiler:
    def compile(self,text,context=None):
        if not text or not text.strip(): raise ValueError('empty goal')
        context=context or {}; t=' '.join(text.strip().split()); gid='goal_'+sha256(t.encode()).hexdigest()[:16]
        risks=self._risks(t); approvals=self._approvals(risks); tree=self._tree(t)
        rb='L4_requires_explicit_approval' if {'money','delete','install'}&set(risks) else ('L3_requires_review_or_confirm' if {'send','external'}&set(risks) else 'L1_auto_allowed_with_audit')
        return GoalContract(gid,t,re.sub(r'^(帮我|给我|请|please)\s*','',t).strip('。.! '),tree,self._constraints(t,context),self._priority(t,rb),self._time(t,context),rb,self._sources(t),self._auto(rb,tree),approvals,['all_task_nodes_terminal','result_verified_against_goal','memory_writeback_done'],datetime.now(timezone.utc).isoformat())
    def _has(self,t,ws): return any(w.lower() in t.lower() for w in ws)
    def _risks(self,t):
        m={'send':['发送','发给','send','短信','邮件'],'money':['付款','支付','转账','购买'],'delete':['删除','清空','覆盖'],'install':['安装','pip install','npm install'],'external':['外部','第三方','api','mcp','connector']}
        r=[k for k,v in m.items() if self._has(t,v)]; return r or ['low']
    def _approvals(self,risks):
        mp={'send':'before_external_message','money':'before_payment','delete':'before_destructive_mutation','install':'before_new_code','external':'before_external_connector'}
        return [mp[x] for x in risks if x in mp]
    def _tree(self,t):
        parts=[p.strip(' 。.!？?') for p in re.split('，|,|；|;|然后|再|并且|以及|and|then',t) if p.strip(' 。.!？?')]
        return [{'node_id':f'g{i+1}','title':p,'depends_on':[] if i==0 else [f'g{i}'],'status':'planned'} for i,p in enumerate(parts[:12] or [t])]
    def _constraints(self,t,c):
        out=['preserve_existing_behavior','audit_all_side_effects']
        if '不要' in t or '不能' in t: out.append('respect_negative_constraints')
        if c.get('no_external'): out.append('no_external_connectors')
        return out
    def _priority(self,t,rb): return 'high' if self._has(t,['马上','立刻','紧急','urgent']) else ('controlled' if rb.startswith('L4') else 'normal')
    def _time(self,t,c):
        if c.get('time_scope'): return c['time_scope']
        for k,ws in {'today':['今天','today'],'tomorrow':['明天'],'week':['本周','下周','week'],'month':['本月','下月']}.items():
            if self._has(t,ws): return k
        return 'unspecified'
    def _sources(self,t):
        s=[]
        if self._has(t,['邮件','邮箱','email']): s.append('email')
        if self._has(t,['日程','会议','calendar']): s.append('calendar')
        if self._has(t,['文件','文档','pdf','zip']): s.append('files')
        if self._has(t,['网页','搜索','查','最新','官网']): s.append('web_or_knowledge')
        return s or ['conversation_context']
    def _auto(self,rb,tree): return [n['node_id'] for n in tree] if rb.startswith('L1') else (['analysis_and_draft_only'] if rb.startswith('L4') else [n['node_id'] for n in tree[:-1]] or ['prepare_draft_only'])
