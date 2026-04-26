"""Change Review - 变更审查 (shim)"""

from typing import Dict, Any


def change_review(change_id: str | None = None) -> Dict[str, Any]:
    """变更审查
    
    Args:
        change_id: 变更ID
        
    Returns:
        审查结果
    """
    return {
        "status": "dry_run",
        "message": "change_review is planned feature",
        "change_id": change_id,
        "approved": False,
        "side_effects": False
    }
