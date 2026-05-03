"""V11.2 Timeout Budget, Retry Policy, and Circuit Breaker."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional
from infrastructure.platform_adapter.runtime_state_store import connect, init_runtime_tables, _now_ms
def init_circuit_tables(db_path: Optional[Path]=None) -> None:
    init_runtime_tables(db_path)
    with connect(db_path) as conn:
        conn.executescript("""CREATE TABLE IF NOT EXISTS runtime_circuit_breakers (scope TEXT PRIMARY KEY,state TEXT NOT NULL,failure_count INTEGER DEFAULT 0,success_count INTEGER DEFAULT 0,opened_at_ms INTEGER DEFAULT 0,cooldown_until_ms INTEGER DEFAULT 0,last_error TEXT,updated_at_ms INTEGER NOT NULL);""")
@dataclass
class RetryDecision:
    allowed: bool; reason: str; retry_after_ms: int=0; max_attempts: int=0; remaining_budget_ms: int=0; side_effecting: bool=False
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
@dataclass
class CircuitState:
    scope: str; state: str; failure_count: int; success_count: int; cooldown_until_ms: int; last_error: Optional[str]
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
class TimeoutBudget:
    def __init__(self,total_budget_ms=60000,per_attempt_ms=15000,max_attempts=3):
        self.total_budget_ms=max(total_budget_ms,1000); self.per_attempt_ms=max(per_attempt_ms,500); self.max_attempts=max(max_attempts,1); self.started_at_ms=_now_ms()
    def remaining_ms(self): return max(0,self.total_budget_ms-(_now_ms()-self.started_at_ms))
    def attempt_timeout_ms(self): return max(500,min(self.per_attempt_ms,self.remaining_ms()))
    def decide_retry(self,*,attempt,side_effecting,result_uncertain=False,last_status="failed"):
        remaining=self.remaining_ms()
        if side_effecting and (result_uncertain or last_status in {"timeout","unknown","partial"}): return RetryDecision(False,"副作用动作结果不确定，禁止静默重试，必须先核验结果",0,self.max_attempts,remaining,side_effecting)
        if attempt>=self.max_attempts: return RetryDecision(False,"达到最大重试次数",0,self.max_attempts,remaining,side_effecting)
        if remaining<=500: return RetryDecision(False,"总超时预算已耗尽",0,self.max_attempts,remaining,side_effecting)
        return RetryDecision(True,"允许低风险/只读动作在预算内重试",min(30000,500*(2**max(attempt-1,0))),self.max_attempts,remaining,side_effecting)
class CircuitBreaker:
    def __init__(self,scope,*,failure_threshold=3,cooldown_ms=120000,db_path=None):
        self.scope=scope; self.failure_threshold=max(failure_threshold,1); self.cooldown_ms=max(cooldown_ms,1000); self.db_path=db_path; init_circuit_tables(db_path)
    def get_state(self):
        now=_now_ms()
        with connect(self.db_path) as conn:
            row=conn.execute("SELECT * FROM runtime_circuit_breakers WHERE scope=?", (self.scope,)).fetchone()
            if not row:
                conn.execute("INSERT INTO runtime_circuit_breakers(scope,state,updated_at_ms) VALUES (?,'closed',?)", (self.scope,now)); row=conn.execute("SELECT * FROM runtime_circuit_breakers WHERE scope=?", (self.scope,)).fetchone()
            if row["state"]=="open" and int(row["cooldown_until_ms"] or 0)<=now:
                conn.execute("UPDATE runtime_circuit_breakers SET state='half_open',updated_at_ms=? WHERE scope=?", (now,self.scope)); row=conn.execute("SELECT * FROM runtime_circuit_breakers WHERE scope=?", (self.scope,)).fetchone()
            return CircuitState(self.scope,row["state"],int(row["failure_count"] or 0),int(row["success_count"] or 0),int(row["cooldown_until_ms"] or 0),row["last_error"])
    def allow_request(self): return self.get_state().state in {"closed","half_open"}
    def record_success(self):
        now=_now_ms()
        with connect(self.db_path) as conn: conn.execute("INSERT INTO runtime_circuit_breakers(scope,state,failure_count,success_count,cooldown_until_ms,updated_at_ms) VALUES (?,'closed',0,1,0,?) ON CONFLICT(scope) DO UPDATE SET state='closed',failure_count=0,success_count=success_count+1,cooldown_until_ms=0,updated_at_ms=excluded.updated_at_ms", (self.scope,now))
        return self.get_state()
    def record_failure(self,error=""):
        now=_now_ms(); current=self.get_state(); failures=current.failure_count+1; state="open" if failures>=self.failure_threshold else "closed"; cooldown=now+self.cooldown_ms if state=="open" else current.cooldown_until_ms
        with connect(self.db_path) as conn: conn.execute("INSERT INTO runtime_circuit_breakers(scope,state,failure_count,success_count,opened_at_ms,cooldown_until_ms,last_error,updated_at_ms) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(scope) DO UPDATE SET state=excluded.state,failure_count=excluded.failure_count,opened_at_ms=CASE WHEN excluded.state='open' THEN excluded.opened_at_ms ELSE opened_at_ms END,cooldown_until_ms=excluded.cooldown_until_ms,last_error=excluded.last_error,updated_at_ms=excluded.updated_at_ms", (self.scope,state,failures,0,now if state=="open" else 0,cooldown,error,now))
        return self.get_state()
def retry_decision_for_action(*,attempt,side_effecting,result_uncertain=False,last_status="failed",total_budget_ms=60000):
    return TimeoutBudget(total_budget_ms=total_budget_ms).decide_retry(attempt=attempt,side_effecting=side_effecting,result_uncertain=result_uncertain,last_status=last_status).to_dict()
