"""查询图库照片能力 - V75.3 修复：必须通过串行化器"""

from typing import Optional, Dict, Any, List


def query_photo(
    photo_id: Optional[str] = None,
    album_id: Optional[str] = None,
    date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    查询图库照片
    
    Args:
        photo_id: 照片ID
        album_id: 相册ID
        date: 日期（YYYY-MM-DD）
        
    Returns:
        照片信息
    """
    # V75.3: 调用端侧图库能力必须通过串行化器
    try:
        from orchestration.device_serial_call import serial_call_device_tool_sync
        
        result = serial_call_device_tool_sync("photo", "query", {
            "photo_id": photo_id,
            "album_id": album_id,
            "date": date
        })
        
        if result.success:
            return result.data or {"success": True, "photos": []}
        else:
            return {"success": False, "error": result.error, "photos": []}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "photos": []
        }


def list_photos(
    limit: int = 20,
    offset: int = 0,
    album_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    列出照片
    
    Args:
        limit: 返回数量限制
        offset: 偏移量
        album_id: 相册ID
        
    Returns:
        照片列表
    """
    try:
        from orchestration.device_serial_call import serial_call_device_tool_sync
        
        result = serial_call_device_tool_sync("photo", "list", {
            "limit": limit,
            "offset": offset,
            "album_id": album_id
        })
        
        if result.success:
            return result.data or {"success": True, "photos": []}
        else:
            return {"success": False, "error": result.error, "photos": []}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "photos": []
        }


def search_photos(
    keyword: str,
    limit: int = 20,
) -> Dict[str, Any]:
    """
    搜索照片
    
    Args:
        keyword: 搜索关键词
        limit: 返回数量限制
        
    Returns:
        搜索结果
    """
    try:
        from orchestration.device_serial_call import serial_call_device_tool_sync
        
        result = serial_call_device_tool_sync("photo", "search", {
            "keyword": keyword,
            "limit": limit
        })
        
        if result.success:
            return result.data or {"success": True, "keyword": keyword, "photos": []}
        else:
            return {"success": False, "error": result.error, "keyword": keyword, "photos": []}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "keyword": keyword,
            "photos": []
        }


def run(**kwargs):
    """能力入口"""
    action = kwargs.pop("action", "query")
    
    if action == "query":
        return query_photo(**kwargs)
    elif action == "list":
        return list_photos(**kwargs)
    elif action == "search":
        return search_photos(**kwargs)
    else:
        return {"success": False, "error": f"未知操作: {action}"}
