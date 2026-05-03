"""
V75.2 设备能力封装集合 - Reality Closure Fix

包含所有端侧能力的统一封装：
- AlarmCapability (闹钟)
- CalendarCapability (日程)
- FileCapability (文件)
- NoteCapability (备忘录)
- ContactCapability (联系人)
- PhotoCapability (照片)
- SMSCapability (短信)
- CollectionCapability (小艺帮记)

V75.2: 所有端侧调用必须通过 DeviceSerialLane
"""

from .base_device_capability import (
    BaseDeviceCapability,
    OperationStatus,
    OperationResult,
    TimeoutProfile
)

# V75.2: 导入串行化器（确保 base_device_capability 使用）
try:
    from orchestration.end_side_serial_lanes_v3 import EndSideSerialLaneV3, DeviceAction
except ImportError:
    EndSideSerialLaneV3 = None
    DeviceAction = None
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import hashlib


class AlarmCapability(BaseDeviceCapability):
    """闹钟能力"""
    
    CAPABILITY_NAME = "alarm"
    
    async def search(self, range_type: str = "next", **kwargs) -> Tuple[List[Dict], OperationResult]:
        """查询闹钟"""
        result = await self._execute_with_verification(
            operation="search",
            params={"rangeType": range_type},
            timeout=TimeoutProfile.SEARCH
        )
        return result.data or [], result
    
    async def create(
        self,
        alarm_time: str,
        alarm_title: str = "",
        check_duplicate: bool = True,
        **kwargs
    ) -> Tuple[Optional[str], OperationResult]:
        """创建闹钟"""
        params = {
            "alarmTime": alarm_time,
            "alarmTitle": alarm_title,
            "checkDuplicate": check_duplicate
        }
        result = await self._execute_with_verification(
            operation="create",
            params=params,
            timeout=TimeoutProfile.CREATE
        )
        entity_id = result.data.get("entityId") if result.data else None
        return entity_id, result
    
    async def modify(
        self,
        entity_id: str,
        new_time: str = None,
        new_title: str = None,
        **kwargs
    ) -> OperationResult:
        """修改闹钟"""
        params = {"entityId": entity_id}
        if new_time:
            params["alarmTime"] = new_time
        if new_title:
            params["alarmTitle"] = new_title
        
        return await self._execute_with_verification(
            operation="modify",
            params=params,
            timeout=TimeoutProfile.MODIFY
        )
    
    async def delete(self, entity_id: str, **kwargs) -> OperationResult:
        """删除闹钟"""
        return await self._execute_with_verification(
            operation="delete",
            params={"entityId": entity_id},
            timeout=TimeoutProfile.DELETE
        )
    
    async def delete_by_title(self, title: str) -> OperationResult:
        """按标题删除闹钟"""
        # 先查询
        alarms, search_result = await self.search()
        if not search_result.is_success():
            return search_result
        
        # 找到匹配的闹钟
        matched = [a for a in alarms if a.get("title") == title]
        if not matched:
            return OperationResult(
                status=OperationStatus.SKIPPED,
                message=f"未找到标题为 '{title}' 的闹钟"
            )
        
        # 删除所有匹配的闹钟
        for alarm in matched:
            result = await self.delete(alarm.get("entityId"))
            if not result.is_success():
                return result
        
        return OperationResult(
            status=OperationStatus.SUCCESS,
            message=f"已删除 {len(matched)} 个闹钟"
        )


class CalendarCapability(BaseDeviceCapability):
    """日程能力"""
    
    CAPABILITY_NAME = "calendar"
    
    async def search(
        self,
        start_time: str = None,
        end_time: str = None,
        keywords: str = None,
        **kwargs
    ) -> Tuple[List[Dict], OperationResult]:
        """查询日程"""
        params = {}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if keywords:
            params["keywords"] = keywords
        
        result = await self._execute_with_verification(
            operation="search",
            params=params,
            timeout=TimeoutProfile.SEARCH
        )
        return result.data or [], result
    
    async def create(
        self,
        event_title: str,
        start_time: str,
        end_time: str = None,
        location: str = None,
        **kwargs
    ) -> Tuple[Optional[str], OperationResult]:
        """创建日程"""
        params = {
            "eventTitle": event_title,
            "startTime": start_time
        }
        if end_time:
            params["endTime"] = end_time
        if location:
            params["location"] = location
        
        result = await self._execute_with_verification(
            operation="create",
            params=params,
            timeout=TimeoutProfile.CREATE
        )
        entity_id = result.data.get("entityId") if result.data else None
        return entity_id, result
    
    async def modify(self, entity_id: str, **kwargs) -> OperationResult:
        """修改日程"""
        params = {"entityId": entity_id}
        params.update(kwargs)
        
        return await self._execute_with_verification(
            operation="modify",
            params=params,
            timeout=TimeoutProfile.MODIFY
        )
    
    async def delete(self, entity_id: str, **kwargs) -> OperationResult:
        """删除日程"""
        return await self._execute_with_verification(
            operation="delete",
            params={"entityId": entity_id},
            timeout=TimeoutProfile.DELETE
        )


class FileCapability(BaseDeviceCapability):
    """文件能力"""
    
    CAPABILITY_NAME = "file"
    
    async def search(self, keywords: str, **kwargs) -> Tuple[List[Dict], OperationResult]:
        """搜索文件"""
        result = await self._execute_with_verification(
            operation="search",
            params={"keywords": keywords},
            timeout=TimeoutProfile.SEARCH
        )
        return result.data or [], result
    
    async def create(self, **kwargs) -> Tuple[Any, OperationResult]:
        """文件不支持创建"""
        return None, OperationResult(
            status=OperationStatus.SKIPPED,
            message="文件能力不支持创建操作"
        )
    
    async def modify(self, **kwargs) -> OperationResult:
        """文件不支持修改"""
        return OperationResult(
            status=OperationStatus.SKIPPED,
            message="文件能力不支持修改操作"
        )
    
    async def delete(self, **kwargs) -> OperationResult:
        """文件不支持删除"""
        return OperationResult(
            status=OperationStatus.SKIPPED,
            message="文件能力不支持删除操作"
        )
    
    async def upload(self, file_path: str) -> Tuple[Optional[str], OperationResult]:
        """上传文件"""
        result = await self._execute_with_verification(
            operation="upload",
            params={"filePath": file_path},
            timeout=TimeoutProfile.CREATE
        )
        url = result.data.get("url") if result.data else None
        return url, result


class NoteCapability(BaseDeviceCapability):
    """备忘录能力"""
    
    CAPABILITY_NAME = "note"
    
    async def search(self, keywords: str = None, **kwargs) -> Tuple[List[Dict], OperationResult]:
        """搜索备忘录"""
        params = {}
        if keywords:
            params["keywords"] = keywords
        
        result = await self._execute_with_verification(
            operation="search",
            params=params,
            timeout=TimeoutProfile.SEARCH
        )
        return result.data or [], result
    
    async def create(
        self,
        title: str,
        content: str,
        **kwargs
    ) -> Tuple[Optional[str], OperationResult]:
        """创建备忘录"""
        result = await self._execute_with_verification(
            operation="create",
            params={"title": title, "content": content},
            timeout=TimeoutProfile.CREATE
        )
        note_id = result.data.get("noteId") if result.data else None
        return note_id, result
    
    async def modify(self, note_id: str, content: str = None, **kwargs) -> OperationResult:
        """修改备忘录"""
        params = {"noteId": note_id}
        if content:
            params["content"] = content
        
        return await self._execute_with_verification(
            operation="modify",
            params=params,
            timeout=TimeoutProfile.MODIFY
        )
    
    async def delete(self, note_id: str, **kwargs) -> OperationResult:
        """删除备忘录"""
        return await self._execute_with_verification(
            operation="delete",
            params={"noteId": note_id},
            timeout=TimeoutProfile.DELETE
        )


class ContactCapability(BaseDeviceCapability):
    """联系人能力"""
    
    CAPABILITY_NAME = "contact"
    
    async def search(self, name: str = None, phone: str = None, **kwargs) -> Tuple[List[Dict], OperationResult]:
        """搜索联系人"""
        params = {}
        if name:
            params["name"] = name
        if phone:
            params["phone"] = phone
        
        result = await self._execute_with_verification(
            operation="search",
            params=params,
            timeout=TimeoutProfile.SEARCH
        )
        return result.data or [], result
    
    async def create(self, **kwargs) -> Tuple[Any, OperationResult]:
        """联系人不支持创建"""
        return None, OperationResult(
            status=OperationStatus.SKIPPED,
            message="联系人能力不支持创建操作"
        )
    
    async def modify(self, **kwargs) -> OperationResult:
        """联系人不支持修改"""
        return OperationResult(
            status=OperationStatus.SKIPPED,
            message="联系人能力不支持修改操作"
        )
    
    async def delete(self, **kwargs) -> OperationResult:
        """联系人不支持删除"""
        return OperationResult(
            status=OperationStatus.SKIPPED,
            message="联系人能力不支持删除操作"
        )
    
    async def call(self, phone: str) -> OperationResult:
        """拨打电话"""
        return await self._execute_with_verification(
            operation="call",
            params={"phone": phone},
            timeout=TimeoutProfile.DEFAULT
        )
    
    async def send_sms(self, phone: str, message: str) -> OperationResult:
        """发送短信"""
        return await self._execute_with_verification(
            operation="send_sms",
            params={"phone": phone, "message": message},
            timeout=TimeoutProfile.CREATE
        )


class PhotoCapability(BaseDeviceCapability):
    """照片能力"""
    
    CAPABILITY_NAME = "photo"
    
    async def search(
        self,
        keywords: str = None,
        start_date: str = None,
        end_date: str = None,
        **kwargs
    ) -> Tuple[List[Dict], OperationResult]:
        """搜索照片"""
        params = {}
        if keywords:
            params["keywords"] = keywords
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        
        result = await self._execute_with_verification(
            operation="search",
            params=params,
            timeout=TimeoutProfile.SEARCH
        )
        return result.data or [], result
    
    async def create(self, **kwargs) -> Tuple[Any, OperationResult]:
        """照片不支持创建"""
        return None, OperationResult(
            status=OperationStatus.SKIPPED,
            message="照片能力不支持创建操作"
        )
    
    async def modify(self, **kwargs) -> OperationResult:
        """照片不支持修改"""
        return OperationResult(
            status=OperationStatus.SKIPPED,
            message="照片能力不支持修改操作"
        )
    
    async def delete(self, **kwargs) -> OperationResult:
        """照片不支持删除"""
        return OperationResult(
            status=OperationStatus.SKIPPED,
            message="照片能力不支持删除操作"
        )


class CollectionCapability(BaseDeviceCapability):
    """小艺帮记能力"""
    
    CAPABILITY_NAME = "collection"
    
    async def search(self, keywords: str = None, **kwargs) -> Tuple[List[Dict], OperationResult]:
        """搜索收藏"""
        params = {}
        if keywords:
            params["keywords"] = keywords
        
        result = await self._execute_with_verification(
            operation="search",
            params=params,
            timeout=TimeoutProfile.SEARCH
        )
        return result.data or [], result
    
    async def create(
        self,
        content: str,
        category: str = None,
        **kwargs
    ) -> Tuple[Optional[str], OperationResult]:
        """添加收藏"""
        params = {"content": content}
        if category:
            params["category"] = category
        
        result = await self._execute_with_verification(
            operation="create",
            params=params,
            timeout=TimeoutProfile.CREATE
        )
        item_id = result.data.get("itemId") if result.data else None
        return item_id, result
    
    async def modify(self, **kwargs) -> OperationResult:
        """收藏不支持修改"""
        return OperationResult(
            status=OperationStatus.SKIPPED,
            message="收藏能力不支持修改操作"
        )
    
    async def delete(self, item_id: str, **kwargs) -> OperationResult:
        """删除收藏"""
        return await self._execute_with_verification(
            operation="delete",
            params={"itemId": item_id},
            timeout=TimeoutProfile.DELETE
        )


# 导出所有能力类
__all__ = [
    "BaseDeviceCapability",
    "OperationStatus",
    "OperationResult",
    "TimeoutProfile",
    "AlarmCapability",
    "CalendarCapability",
    "FileCapability",
    "NoteCapability",
    "ContactCapability",
    "PhotoCapability",
    "CollectionCapability",
]
