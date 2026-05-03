#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = [
    'infrastructure/context_resume.py','scripts/resume_current_task.py','scripts/context_resume_smoke.py',
    'agent_kernel/architecture_boundary.py','agent_kernel/hub_boundary_contract.py','orchestration/device_workflow_serial_policy.py','execution/device_action_timeout_verifier.py','infrastructure/compact_resume_policy.py','governance/policy/organ_conflict_policy.py','scripts/v23_2_to_v23_6_all_smoke.py',
    'execution/action_idempotency_guard.py','execution/device_receipt_reconciler.py','orchestration/three_way_reminder_transaction.py','orchestration/end_side_workflow_contract.py','infrastructure/progress_heartbeat.py','governance/policy/failure_taxonomy.py','scripts/v23_7_to_v24_6_all_smoke.py','scripts/v24_6_end_side_stability_gate.py',
    'orchestration/end_side_global_serial_executor.py','governance/policy/end_side_global_serial_policy.py','scripts/v24_7_end_side_global_serial_smoke.py','scripts/v24_7_end_side_global_serial_gate.py',
    'agent_kernel/layer_integrity_gate_v2.py','agent_kernel/personal_operating_loop_v2.py','core/goal_contract_v2.py','orchestration/durable_task_graph_v2.py','memory_context/memory_writeback_guard_v2.py','world_interface/world_interface_resolver_v2.py','capability_extension/capability_extension_sandbox_gate_v2.py','scripts/v24_8_to_v25_7_all_smoke.py','scripts/v25_7_personal_operating_agent_gate.py',
    'core/operating_contract_v3.py','orchestration/durable_workflow_engine_v3.py','orchestration/end_side_serial_lanes_v3.py','memory_context/personal_memory_kernel_v4.py','governance/constitutional_judge_v4.py','world_interface/universal_world_resolver_v4.py','capability_extension/controlled_extension_pipeline_v4.py','evaluation/autonomy_regression_matrix_v4.py','agent_kernel/persona_drift_guard_v4.py','agent_kernel/autonomous_os_mission_control_v4.py','scripts/v26_0_to_v35_0_all_smoke.py','scripts/v35_0_autonomous_os_gate.py'
]
def main() -> int:
    missing = [p for p in REQUIRED_PATHS if not (ROOT / p).exists()]
    ok = not missing
    report = {
        'gate': 'v23_to_v35_full_replace_gate',
        'status': 'pass' if ok else 'fail',
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'required_count': len(REQUIRED_PATHS),
        'missing': missing,
        'rules': {
            'full_replace_package': True,
            'contains_v23_1_to_v35_0_outputs': True,
            'agent_kernel_layer': 'L3 Orchestration, not L7',
            'end_side_multi_action_policy': 'global serial',
            'action_timeout_policy': 'pending_verify, not device_offline'
        }
    }
    (ROOT / 'V23_TO_V35_FULL_REPLACE_GATE_REPORT.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1
if __name__ == '__main__':
    raise SystemExit(main())
