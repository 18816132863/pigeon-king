#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${1:-$(pwd)}"
PATCH_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$PROJECT_ROOT/v86_backup_$STAMP"

mkdir -p "$BACKUP_DIR"

copy_with_backup() {
  local rel="$1"
  local src="$PATCH_ROOT/$rel"
  local dst="$PROJECT_ROOT/$rel"
  if [ -f "$dst" ]; then
    mkdir -p "$BACKUP_DIR/$(dirname "$rel")"
    cp "$dst" "$BACKUP_DIR/$rel"
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
}

copy_with_backup "orchestration/workflow/workflow_engine.py"
copy_with_backup "orchestration/workflow/parallel_policy.py"
copy_with_backup "orchestration/workflow/parallel_executor.py"
copy_with_backup "orchestration/state/workflow_event_store.py"
copy_with_backup "tests/test_workflow_controlled_parallel.py"
copy_with_backup "tests/test_workflow_parallel_commit_barrier.py"
copy_with_backup "tests/test_workflow_parallel_serial_lane.py"
copy_with_backup "tests/test_workflow_parallel_deterministic_replay.py"
copy_with_backup "docs/V86_CONTROLLED_PARALLEL_FINAL.md"

echo "V86 controlled parallel patch installed. Backup: $BACKUP_DIR"
echo "Run: pytest tests/test_workflow_controlled_parallel.py tests/test_workflow_parallel_commit_barrier.py tests/test_workflow_parallel_serial_lane.py tests/test_workflow_parallel_deterministic_replay.py -q"
