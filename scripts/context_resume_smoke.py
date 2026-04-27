#!/usr/bin/env python3
"""Smoke test for Context Resume: interruption, reload, no duplicate execution."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from infrastructure.context_resume import ContextResumeStore


def assert_true(value, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="context_resume_smoke_"))
    try:
        store = ContextResumeStore(tmp)
        state = store.start_task(
            task_id="smoke-context-resume",
            current_version="V23.1-context-resume",
            current_phase="build_package",
            pending_steps=["extract", "patch", "package"],
            next_command="/usr/bin/python3 scripts/resume_current_task.py",
            last_output_file="reports/partial.json",
            metadata={"purpose": "prove resume does not require chat context"},
        )
        assert_true(state.pending_steps == ["extract", "patch", "package"], "initial pending steps mismatch")

        store.complete_step("extract", last_output_file="reports/extract.json")
        store.mark_interrupted("simulated_context_compaction")

        reloaded = ContextResumeStore(tmp)
        payload = reloaded.resume_payload()
        assert_true(payload["should_resume"] is True, "should_resume must be true after interruption")
        assert_true(payload["completed_steps"] == ["extract"], "completed step lost")
        assert_true(payload["pending_steps"] == ["patch", "package"], "pending steps not preserved")
        assert_true(payload["next_command"] == "/usr/bin/python3 scripts/resume_current_task.py", "next command lost")
        assert_true("聊天历史" in payload["resume_instruction"], "resume instruction must forbid history replay")

        # Duplicate completion should not duplicate completed_steps.
        reloaded.complete_step("extract")
        payload2 = reloaded.resume_payload()
        assert_true(payload2["completed_steps"].count("extract") == 1, "duplicate step was written")

        reloaded.mark_running()
        reloaded.heartbeat()
        reloaded.complete_step("patch")
        reloaded.complete_step("package")
        final = reloaded.resume_payload()
        assert_true(final["status"] == "completed", "task did not complete")
        assert_true(final["pending_steps"] == [], "pending steps not empty")

        report = {
            "context_resume_smoke": "pass",
            "state_file": str(tmp / "task_state" / "current_task_state.json"),
            "event_log_exists": (tmp / "task_state" / "context_resume_events.jsonl").exists(),
            "guarantees": [
                "state survives interruption",
                "pending steps are preserved",
                "completed steps are not duplicated",
                "next command is preserved",
                "resume does not require chat context",
            ],
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
