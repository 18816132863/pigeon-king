#!/usr/bin/env python3
"""Resume helper for tasks interrupted by context compaction or UI stalls."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from infrastructure.context_resume import ContextResumeStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Read or update task_state/current_task_state.json")
    parser.add_argument("--json", action="store_true", help="print JSON payload")
    parser.add_argument("--heartbeat", action="store_true", help="write a heartbeat and exit")
    parser.add_argument("--mark-running", action="store_true", help="mark interrupted task as running")
    parser.add_argument("--mark-interrupted", metavar="REASON", help="mark task interrupted with reason")
    parser.add_argument("--complete-step", metavar="STEP", help="mark one step completed without duplicating it")
    parser.add_argument("--phase", metavar="PHASE", help="update current phase")
    parser.add_argument("--next-command", metavar="COMMAND", help="update next command")
    parser.add_argument("--last-output", metavar="PATH", help="update last output file")
    parser.add_argument("--state-path", metavar="PATH", help="custom state file path")
    args = parser.parse_args()

    store = ContextResumeStore(ROOT, state_path=args.state_path) if args.state_path else ContextResumeStore(ROOT)

    if not store.exists():
        payload = {
            "should_resume": False,
            "error": "missing task_state/current_task_state.json",
            "hint": "先用 ContextResumeStore.start_task(...) 或长任务入口写入状态文件。",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload["hint"])
        return 2

    if args.heartbeat:
        store.heartbeat()
    if args.mark_interrupted:
        store.mark_interrupted(args.mark_interrupted)
    if args.mark_running:
        store.mark_running()
    if args.phase or args.next_command is not None or args.last_output is not None:
        state = store.require_state()
        store.update_phase(
            args.phase or state.current_phase,
            next_command=args.next_command,
            last_output_file=args.last_output,
        )
    if args.complete_step:
        store.complete_step(args.complete_step, last_output_file=args.last_output)

    if args.json:
        print(json.dumps(store.resume_payload(), ensure_ascii=False, indent=2))
    else:
        print(store.resume_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
