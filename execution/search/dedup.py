"""结果去重增强 - 语义去重"""
from typing import List, Dict, Any, Optional, Union
import hashlib

class SemanticDeduplicator:
    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
    
    @staticmethod
    def content_hash(content: str) -> str:
        """内容哈希"""
        # 标准化内容
        normalized = content.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:8]
    
    @staticmethod
    def simple_similarity(text1: str, text2: str) -> float:
        """简单相似度计算（基于词重叠）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def deduplicate(self, results: List[Dict]) -> List[Dict]:
        """语义去重"""
        if not results:
            return results
        
        deduplicated = []
        seen_hashes = set()
        
        for result in results:
            content = result.get('content', '')
            content_hash = self.content_hash(content)
            
            # 完全重复检查
            if content_hash in seen_hashes:
                continue
            
            # 语义相似检查
            is_duplicate = False
            for existing in deduplicated:
                existing_content = existing.get('content', '')
                similarity = self.simple_similarity(content, existing_content)
                
                if similarity >= self.threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(result)
                seen_hashes.add(content_hash)
        
        return deduplicated


class Deduplicator:
    """向后兼容的去重器 —— 支持 list[str]、list[dict]、普通对象。

    不依赖外部 API，完全本地执行。
    """

    _DICT_KEY_ORDER = ("id", "name", "path", "title", "text", "content", "url")

    def __init__(self, key_fields: Optional[Union[str, List[str]]] = None, case_sensitive: bool = True):
        self.case_sensitive = case_sensitive
        if key_fields is None:
            self.key_fields: List[str] = []
        elif isinstance(key_fields, str):
            self.key_fields = [key_fields]
        else:
            self.key_fields = list(key_fields)

    def _item_key(self, item: Any) -> str:
        """从任意 item 生成去重 key。"""
        if isinstance(item, dict):
            # 优先用指定字段，否则用预定义顺序，再不行用整个 dict repr
            parts: List[str] = []
            fields = self.key_fields if self.key_fields else self._DICT_KEY_ORDER
            for f in fields:
                v = item.get(f)
                if v is not None:
                    parts.append(str(v))
            if parts:
                key = "|".join(parts)
            else:
                key = repr(sorted(item.items()))
        elif isinstance(item, str):
            key = item
        else:
            key = repr(item)

        if not self.case_sensitive:
            key = key.lower()
        return hashlib.md5(key.encode("utf-8")).hexdigest()

    def deduplicate(self, items: List[Any]) -> List[Any]:
        """去重，保持首次出现顺序。"""
        if not items:
            return items
        seen: set = set()
        result: List[Any] = []
        for item in items:
            key = self._item_key(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    def __call__(self, items: List[Any]) -> List[Any]:
        return self.deduplicate(items)
