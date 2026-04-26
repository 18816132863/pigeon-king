#!/usr/bin/env python3
from pathlib import Path
import sys, os, tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_adapter.timeout_circuit import TimeoutBudget, CircuitBreaker
def main():
    db=Path(tempfile.gettempdir())/"pigeon_v11_2_smoke.db"
    if db.exists(): db.unlink()
    budget=TimeoutBudget(total_budget_ms=5000,max_attempts=3)
    side=budget.decide_retry(attempt=1,side_effecting=True,result_uncertain=True,last_status="timeout")
    assert side.allowed is False
    readonly=budget.decide_retry(attempt=1,side_effecting=False)
    assert readonly.allowed is True
    cb=CircuitBreaker("smoke:adapter",failure_threshold=2,cooldown_ms=60000,db_path=db)
    assert cb.allow_request() is True
    cb.record_failure("timeout"); state=cb.record_failure("timeout")
    assert state.state=="open" and cb.allow_request() is False
    print({"ok":True,"side_effect_retry":side.to_dict(),"readonly_retry":readonly.to_dict(),"circuit":state.to_dict()})
if __name__=="__main__":
    main(); os._exit(0)
