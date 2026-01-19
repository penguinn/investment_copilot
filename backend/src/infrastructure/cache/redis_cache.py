import json
import logging
from datetime import date, datetime
from typing import Any, Optional, Union

import redis
from redis.exceptions import RedisError
from src.config import REDIS_RETRY, REDIS_TIMEOUT, REDIS_URL

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，处理 datetime 对象"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


class RedisCache:
    """Redis缓存服务"""

    def __init__(self):
        self.client = redis.from_url(
            REDIS_URL,
            socket_timeout=REDIS_TIMEOUT,
            socket_connect_timeout=REDIS_TIMEOUT,
            retry_on_timeout=REDIS_RETRY,
        )

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Redis get error: {str(e)}")
            return None

    async def set(self, key: str, value: Any, timeout: int = 300) -> bool:
        """设置缓存，默认过期时间5分钟"""
        try:
            return self.client.setex(
                key, timeout, json.dumps(value, ensure_ascii=False, cls=DateTimeEncoder)
            )
        except (RedisError, TypeError) as e:
            logger.error(f"Redis set error: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            return bool(self.client.delete(key))
        except RedisError as e:
            logger.error(f"Redis delete error: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return bool(self.client.exists(key))
        except RedisError as e:
            logger.error(f"Redis exists error: {str(e)}")
            return False


# 创建一个全局实例，方便直接导入使用
cache = RedisCache()
