"""Response Formatter - 格式化响应"""


def format_response(result: dict) -> dict:
    """格式化处理结果
    
    Args:
        result: 处理结果字典
        
    Returns:
        格式化后的响应字典
    """
    return {
        "status": result.get("status", "ok"),
        "data": result,
        "formatted": True
    }
