from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime,timezone
import sqlite3,json
@dataclass
class TaskNode:
    node_id:str; title:str; action:str='execute'; depends_on:list=None; risk:str='L1'; status:str='pending'; output:dict=None
    def __post_init__(self): self.depends_on=self.depends_on or []
@dataclass
class TaskGraph: graph_id:str; goal_id:str; nodes:list; done_definition:list
class TaskGraphStore:
    def __init__(self,db=':memory:'):
        self.conn=sqlite3.connect(str(db)); self.conn.execute('CREATE TABLE IF NOT EXISTS graphs(id TEXT PRIMARY KEY,payload TEXT)'); self.conn.execute('CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,graph_id TEXT,node_id TEXT,status TEXT,detail TEXT,created_at TEXT)'); self.conn.commit()
    def save(self,g): self.conn.execute('INSERT OR REPLACE INTO graphs VALUES(?,?)',(g.graph_id,json.dumps({'graph_id':g.graph_id,'goal_id':g.goal_id,'done_definition':g.done_definition,'nodes':[asdict(n) for n in g.nodes]},ensure_ascii=False))); self.conn.commit()
    def load(self,gid):
        r=self.conn.execute('SELECT payload FROM graphs WHERE id=?',(gid,)).fetchone();
        if not r: raise KeyError(gid)
        d=json.loads(r[0]); return TaskGraph(d['graph_id'],d['goal_id'],[TaskNode(**n) for n in d['nodes']],d.get('done_definition',[]))
    def event(self,gid,nid,st,detail=''):
        self.conn.execute('INSERT INTO events(graph_id,node_id,status,detail,created_at) VALUES(?,?,?,?,?)',(gid,nid,st,json.dumps(detail,ensure_ascii=False) if not isinstance(detail,str) else detail,datetime.now(timezone.utc).isoformat())); self.conn.commit()
class TaskGraphBuilder:
    def from_goal(self,goal):
        last=(goal.get('objective_tree') or [{'node_id':'g1'}])[-1]['node_id']; approvals=bool(goal.get('approval_points'))
        nodes=[TaskNode(i['node_id'],i.get('title',i['node_id']),'approval_interrupt' if approvals and i['node_id']==last else 'execute',i.get('depends_on',[]),'L3' if approvals else 'L1') for i in goal.get('objective_tree',[])] or [TaskNode('g1',goal.get('objective','execute'))]
        return TaskGraph('graph_'+goal['goal_id'].split('goal_',1)[-1],goal['goal_id'],nodes,goal.get('done_definition',[]))
class TaskGraphExecutor:
    def __init__(self,store,handlers=None): self.store=store; self.handlers=handlers or {}
    def run(self,g,approvals=None):
        approvals=set(approvals or []); m={n.node_id:n for n in g.nodes}; changed=True
        while changed:
            changed=False
            for n in g.nodes:
                if n.status!='pending' or any(m[d].status!='completed' for d in n.depends_on): continue
                if n.action=='approval_interrupt' and n.node_id not in approvals:
                    n.status='blocked_for_approval'; self.store.event(g.graph_id,n.node_id,n.status,{'reason':'approval required'}); changed=True; continue
                n.status='completed'; n.output={'ok':True,'node_id':n.node_id}; self.store.event(g.graph_id,n.node_id,n.status,n.output); changed=True
            self.store.save(g)
        return self.summary(g)
    def resume(self,gid,approvals=None):
        g=self.store.load(gid)
        for n in g.nodes:
            if n.status=='blocked_for_approval' and approvals and n.node_id in approvals: n.status='pending'
        return self.run(g,approvals)
    def summary(self,g):
        s={}
        for n in g.nodes: s[n.status]=s.get(n.status,0)+1
        return {'graph_id':g.graph_id,'goal_id':g.goal_id,'statuses':s,'terminal':all(n.status in {'completed','failed','blocked_for_approval'} for n in g.nodes),'success':all(n.status=='completed' for n in g.nodes)}
