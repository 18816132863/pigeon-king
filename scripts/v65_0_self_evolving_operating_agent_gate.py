#!/usr/bin/env python3
from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent_kernel.v56_to_v65_operating_agent import SelfEvolvingOperatingAgentV6, DeviceActionV6

def main():
    agent = SelfEvolvingOperatingAgentV6(); checks = {}
    checks["agent_kernel_layer_is_l3"] = agent.architecture_layer == "L3 Orchestration"
    plan = agent.plan("完成一个低风险端侧提醒任务")
    checks["mission_contract_created"] = bool(plan["contract"]["mission_id"])
    checks["judge_allows_safe_contract"] = plan["judge"]["decision"] == "allow"
    receipt = agent.execute_device_action(DeviceActionV6("a1", "create_alarm", "alarm:meal:0800"), lambda a: {"status":"success"})
    checks["device_action_serial_receipt"] = receipt["status"] == "success" and not agent.device_lane.locked
    checks["memory_writeback_guarded"] = agent.write_memory("低风险提醒任务已成功执行并写回经验", confidence=0.9)["decision"] == "committed"
    ok = all(checks.values())
    report = {"v65_0_self_evolving_operating_agent_gate": "pass" if ok else "fail", "checks": checks}
    (ROOT / "V65_0_SELF_EVOLVING_OPERATING_AGENT_GATE.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False)); raise SystemExit(0 if ok else 1)
if __name__ == "__main__":
    main()
