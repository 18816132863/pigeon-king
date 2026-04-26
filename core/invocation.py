"""Invocation Status Explainer - 调用状态解释器 (shim)"""

from typing import Dict, Any


def explain_status(invocation_id: str | None = None) -> Dict[str, Any]:
    """解释调用状态
    
    Args:
        invocation_id: 调用ID
        
    Returns:
        状态解释
    """
    return {
        "status": "dry_run",
        "message": "explain_status is planned feature",
        "invocation_id": invocation_id,
        "side_effects": False
    }
