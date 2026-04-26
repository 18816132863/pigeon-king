"""Task Replay - 任务重放 (shim)"""

from typing import Dict, Any


def replay_run(run_id: str | None = None) -> Dict[str, Any]:
    """重放任务运行
    
    Args:
        run_id: 运行ID
        
    Returns:
        重放结果
    """
    return {
        "status": "dry_run",
        "message": "replay_run is planned feature",
        "run_id": run_id,
        "steps": [],
        "side_effects": False
    }
