param(
  [string]$ProjectRoot = (Get-Location).Path
)

$PatchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $ProjectRoot "v86_backup_$Stamp"
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

function Copy-WithBackup([string]$Rel) {
  $Src = Join-Path $PatchRoot $Rel
  $Dst = Join-Path $ProjectRoot $Rel
  if (Test-Path $Dst) {
    $BackupPath = Join-Path $BackupDir $Rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $BackupPath) | Out-Null
    Copy-Item $Dst $BackupPath -Force
  }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dst) | Out-Null
  Copy-Item $Src $Dst -Force
}

Copy-WithBackup "orchestration/workflow/workflow_engine.py"
Copy-WithBackup "orchestration/workflow/parallel_policy.py"
Copy-WithBackup "orchestration/workflow/parallel_executor.py"
Copy-WithBackup "orchestration/state/workflow_event_store.py"
Copy-WithBackup "tests/test_workflow_controlled_parallel.py"
Copy-WithBackup "tests/test_workflow_parallel_commit_barrier.py"
Copy-WithBackup "tests/test_workflow_parallel_serial_lane.py"
Copy-WithBackup "tests/test_workflow_parallel_deterministic_replay.py"
Copy-WithBackup "docs/V86_CONTROLLED_PARALLEL_FINAL.md"

Write-Host "V86 controlled parallel patch installed. Backup: $BackupDir"
Write-Host "Run: pytest tests/test_workflow_controlled_parallel.py tests/test_workflow_parallel_commit_barrier.py tests/test_workflow_parallel_serial_lane.py tests/test_workflow_parallel_deterministic_replay.py -q"
