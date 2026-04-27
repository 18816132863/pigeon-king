#!/usr/bin/env python3
"""Smoke test for V24.7 End-side Global Serial Executor."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from orchestration.end_side_global_serial_executor import DeviceAction, DeviceActionState, EndSideGlobalSerialExecutor, make_device_action
from governance.policy.end_side_global_serial_policy import assert_all_end_side_actions_serialized

def main() -> int:
    execution_order = []
    def backend(action: DeviceAction):
        execution_order.append(action.capability_name)
        if action.capability_name == 'modify_alarm':
            return {'ok': False, 'timeout': True, 'device_connection_state': 'connected', 'verified_after_timeout': False}
        return {'ok': True, 'device_connection_state': 'connected'}
    actions = [
        make_device_action('alarm', 'search_alarm', {'rangeType': 'next'}, idempotency_key='alarm-search-next', timeout_seconds=20),
        make_device_action('alarm', 'modify_alarm', {'entityId': '120'}, idempotency_key='alarm-modify-120', timeout_seconds=90),
        make_device_action('notification', 'hiboard_push', {'title': '吃饭提醒'}, idempotency_key='hiboard-eat-reminder'),
        make_device_action('calendar', 'create_calendar_reminder', {'title': '吃饭提醒'}, idempotency_key='calendar-eat-reminder'),
        make_device_action('gui_action', 'gui_alarm_fallback', {'title': '吃饭提醒'}, idempotency_key='gui-fallback-eat-reminder'),
        make_device_action('settings', 'read_device_setting', {'name': 'battery'}, idempotency_key='settings-battery'),
        make_device_action('notification', 'hiboard_push', {'title': '吃饭提醒'}, idempotency_key='hiboard-eat-reminder'),
    ]
    assert_all_end_side_actions_serialized([a.action_type for a in actions], used_global_serial_executor=True)
    executor = EndSideGlobalSerialExecutor(transaction_id='v24_7_smoke', backend=backend)
    executor.enqueue_many(actions)
    receipts = executor.run_all()
    expected_order = ['search_alarm', 'modify_alarm', 'hiboard_push', 'create_calendar_reminder', 'gui_alarm_fallback', 'read_device_setting']
    assert execution_order == expected_order, execution_order
    assert executor.parallel_violation_count == 0
    assert [r.sequence_no for r in receipts] == list(range(1, len(receipts)+1))
    by_capability = {r.capability_name: r for r in receipts}
    assert by_capability['search_alarm'].state == DeviceActionState.SUCCESS
    assert by_capability['modify_alarm'].state == DeviceActionState.TIMEOUT_PENDING_VERIFY
    assert by_capability['modify_alarm'].result['device_connection_state'] == 'connected'
    assert 'offline' not in json.dumps(by_capability['modify_alarm'].to_dict(), ensure_ascii=False).lower()
    assert receipts[-1].state == DeviceActionState.SKIPPED_DUPLICATE
    report = {
        'v24_7_end_side_global_serial_smoke': 'pass',
        'transaction_id': executor.transaction_id,
        'execution_order': execution_order,
        'parallel_violation_count': executor.parallel_violation_count,
        'timeout_state': by_capability['modify_alarm'].state.value,
        'duplicate_state': receipts[-1].state.value,
        'receipts': [r.to_dict() for r in receipts],
    }
    (ROOT/'V24_7_END_SIDE_GLOBAL_SERIAL_SMOKE_REPORT.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
