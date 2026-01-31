"""
短期记忆 - 对话历史管理
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis

from src.config import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT, REDIS_DB

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    短期记忆（对话历史）
    - 存储当前会话的对话历史
    - 使用 Redis 存储，支持 TTL 过期
    - 限制历史长度，避免 token 超限
    """

    def __init__(
        self,
        session_id: str,
        max_messages: int = 20,
        ttl_seconds: int = 3600,  # 1小时过期
    ):
        """
        初始化短期记忆
        :param session_id: 会话ID
        :param max_messages: 最大消息数量
        :param ttl_seconds: 过期时间（秒）
        """
        self.session_id = session_id
        self.max_messages = max_messages
        self.ttl_seconds = ttl_seconds
        self._redis = None
        self._cache_key = f"agent:conversation:{session_id}"

    @property
    def redis_client(self):
        """延迟初始化 Redis 客户端"""
        if self._redis is None:
            self._redis = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
                db=REDIS_DB,
                decode_responses=True,
            )
        return self._redis

    def add_message(self, role: str, content: str, **metadata):
        """
        添加消息到对话历史
        :param role: 角色 (user/assistant/system/tool)
        :param content: 消息内容
        :param metadata: 额外元数据
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **metadata,
        }

        try:
            # 获取现有历史
            history = self.get_messages()

            # 添加新消息
            history.append(message)

            # 限制长度（保留最近的消息）
            if len(history) > self.max_messages:
                history = history[-self.max_messages:]

            # 保存到 Redis
            self.redis_client.setex(
                self._cache_key,
                self.ttl_seconds,
                json.dumps(history, ensure_ascii=False),
            )

        except Exception as e:
            logger.error(f"Failed to add message to memory: {e}")

    def get_messages(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        try:
            data = self.redis_client.get(self._cache_key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
        return []

    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """
        获取适合发送给 LLM 的消息格式
        只保留 role 和 content 字段
        """
        messages = self.get_messages()
        return [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m["role"] in ("user", "assistant", "system")
        ]

    def clear(self):
        """清空对话历史"""
        try:
            self.redis_client.delete(self._cache_key)
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")

    def get_summary(self) -> str:
        """
        获取对话摘要（用于长期记忆）
        """
        messages = self.get_messages()
        if not messages:
            return ""

        # 提取关键信息
        user_queries = [m["content"] for m in messages if m["role"] == "user"]
        return f"用户查询: {'; '.join(user_queries[-3:])}"  # 最近3条查询
