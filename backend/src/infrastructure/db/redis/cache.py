import json
from abc import ABC, abstractmethod
from typing import Any, Optional

from django.core.cache import cache


class BaseCache(ABC):
    """缓存基类"""

    def __init__(self, prefix: str):
        self.prefix = prefix

    def _get_key(self, key: str) -> str:
        """获取缓存key"""
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        data = cache.get(self._get_key(key))
        return json.loads(data) if data else None

    async def set(self, key: str, value: Any, timeout: int = 300) -> None:
        """设置缓存"""
        cache.set(self._get_key(key), json.dumps(value), timeout)

    async def delete(self, key: str) -> None:
        """删除缓存"""
        cache.delete(self._get_key(key))

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return cache.has_key(self._get_key(key))
