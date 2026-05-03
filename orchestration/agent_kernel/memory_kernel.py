from dataclasses import dataclass,asdict
from datetime import datetime,timezone
import sqlite3,json
VALID={'semantic','episodic','procedural','profile','preference'}
@dataclass
class MemoryRecord:
    memory_id:str; memory_type:str; content:str; tags:list; confidence:float=.7; source:str='agent_kernel'; status:str='active'; created_at:str=''
    def __post_init__(self):
        if self.memory_type not in VALID: raise ValueError('invalid memory_type')
        if not self.created_at: self.created_at=datetime.now(timezone.utc).isoformat()
class PersonalMemoryKernel:
    def __init__(self,db=':memory:'):
        self.conn=sqlite3.connect(str(db)); self.conn.execute('CREATE TABLE IF NOT EXISTS memories(id TEXT PRIMARY KEY,type TEXT,content TEXT,tags TEXT,confidence REAL,source TEXT,status TEXT,created_at TEXT)'); self.conn.commit()
    def add(self,r): self.conn.execute('INSERT OR REPLACE INTO memories VALUES(?,?,?,?,?,?,?,?)',(r.memory_id,r.memory_type,r.content,json.dumps(r.tags,ensure_ascii=False),r.confidence,r.source,r.status,r.created_at)); self.conn.commit(); return r.memory_id
    def search(self,q='',memory_type=None,min_confidence=0,limit=20):
        sql="SELECT * FROM memories WHERE status='active' AND confidence>=?"; params=[min_confidence]
        if memory_type: sql+=' AND type=?'; params.append(memory_type)
        if q: sql+=' AND (content LIKE ? OR tags LIKE ?)'; params += [f'%{q}%',f'%{q}%']
        sql+=' ORDER BY confidence DESC LIMIT ?'; params.append(limit)
        return [{'memory_id':r[0],'memory_type':r[1],'content':r[2],'tags':json.loads(r[3]),'confidence':r[4],'source':r[5],'status':r[6],'created_at':r[7]} for r in self.conn.execute(sql,params).fetchall()]
    def writeback_from_task(self,goal,summary):
        gid=goal.get('goal_id','goal_unknown'); ids=[self.add(MemoryRecord('episodic_'+gid,'episodic',json.dumps(summary,ensure_ascii=False),['task',gid],.8,'task_graph'))]
        if summary.get('success'): ids.append(self.add(MemoryRecord('procedural_success_'+gid,'procedural','reuse goal->judge->task_graph->verify->memory flow',['procedure',gid],.65,'task_graph')))
        return ids
