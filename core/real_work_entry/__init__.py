"""
V23.2 Real Work Entry.

This layer makes the certified Final AI Shape V2 become the default real-task
entrypoint:

received message -> AIShapeCore -> GoalContract -> TaskGraph -> Judge ->
WorldInterface -> ActionLog -> Checkpoint -> MemoryWriteback -> Final Report.

It does not directly create unapproved external side effects. External send,
delete, install, payment, secret or credential actions are represented as
approval tasks or blocked tasks.
"""

from .schemas import (
    EntryStatus,
    ActionLogStatus,
    RealWorkRequest,
    ActionLogRecord,
    RealWorkReport,
)
from .action_log import ActionLogStore
from .message_entry import RealWorkMessageEntry
from .real_work_entry import RealWorkEntry, YuanLingRealWorkEntry, init_real_work_entry, run_real_work_entry

__all__ = [
    "EntryStatus",
    "ActionLogStatus",
    "RealWorkRequest",
    "ActionLogRecord",
    "RealWorkReport",
    "ActionLogStore",
    "RealWorkMessageEntry",
    "RealWorkEntry",
    "YuanLingRealWorkEntry",
    "init_real_work_entry",
    "run_real_work_entry",
]
