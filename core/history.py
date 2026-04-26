"""History Export - 历史导出 (shim)"""

from typing import Dict, Any


def export_history(format: str = "json") -> Dict[str, Any]:
    """导出历史
    
    Args:
        format: 导出格式
        
    Returns:
        导出结果
    """
    return {
        "status": "dry_run",
        "message": "export_history is planned feature",
        "format": format,
        "records": [],
        "side_effects": False
    }
