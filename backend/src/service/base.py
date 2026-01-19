"""
服务基类
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.infrastructure.cache.redis_cache import cache
from src.config import CACHE_TTL_REALTIME, CACHE_TTL_DAILY

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """服务基类"""

    def __init__(self, cache_prefix: str):
        self.cache = cache
        self.cache_prefix = cache_prefix

    def _cache_key(self, *args) -> str:
        """生成缓存键"""
        return f"{self.cache_prefix}:{':'.join(str(a) for a in args)}"

    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取数据"""
        try:
            return await self.cache.get(key)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
            return None

    async def _set_to_cache(self, key: str, value: Any, ttl: int = CACHE_TTL_REALTIME) -> bool:
        """设置缓存"""
        try:
            return await self.cache.set(key, value, timeout=ttl)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
            return False

    async def _delete_from_cache(self, key: str) -> bool:
        """删除缓存"""
        try:
            return await self.cache.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete failed: {e}")
            return False
