"""Task Preview - 任务预览 (shim)"""

from typing import Dict, Any


def preview_task(task_id: str | None = None) -> Dict[str, Any]:
    """预览任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        预览结果
    """
    return {
        "status": "dry_run",
        "message": "preview_task is planned feature",
        "task_id": task_id,
        "preview": {},
        "side_effects": False
    }
