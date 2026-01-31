"""
长期记忆 - 用户偏好和历史投资建议存储
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.infrastructure.db.database import sync_engine
from src.infrastructure.db.pgsql import AgentMemory

logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    长期记忆管理
    - 存储用户偏好（关注的板块、风险偏好等）
    - 存储历史投资建议
    - 存储重要洞察
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id

    def add_memory(
        self,
        memory_type: str,
        content: str,
        metadata: Dict[str, Any] = None,
        importance: int = 1,
    ) -> bool:
        """
        添加长期记忆
        :param memory_type: 类型 (preference/recommendation/insight)
        :param content: 内容
        :param metadata: 元数据
        :param importance: 重要性 (1-5)
        """
        try:
            with Session(sync_engine) as session:
                memory = AgentMemory(
                    user_id=self.user_id,
                    memory_type=memory_type,
                    content=content,
                    extra_data=json.dumps(metadata, ensure_ascii=False) if metadata else None,
                    importance=importance,
                )
                session.add(memory)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return False

    def get_memories(
        self,
        memory_type: str = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取长期记忆
        :param memory_type: 类型过滤
        :param limit: 返回数量
        """
        try:
            with Session(sync_engine) as session:
                query = select(AgentMemory).where(
                    AgentMemory.user_id == self.user_id
                )

                if memory_type:
                    query = query.where(AgentMemory.memory_type == memory_type)

                query = query.order_by(
                    desc(AgentMemory.importance),
                    desc(AgentMemory.created_at),
                ).limit(limit)

                result = session.execute(query)
                memories = result.scalars().all()

                return [
                    {
                        "id": m.id,
                        "type": m.memory_type,
                        "content": m.content,
                        "metadata": json.loads(m.extra_data) if m.extra_data else None,
                        "importance": m.importance,
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                    }
                    for m in memories
                ]
        except Exception as e:
            logger.error(f"Failed to get memories: {e}")
            return []

    def get_user_preferences(self) -> Dict[str, Any]:
        """获取用户偏好"""
        memories = self.get_memories(memory_type="preference", limit=5)
        if not memories:
            return {}

        # 合并所有偏好
        preferences = {}
        for m in memories:
            if m.get("metadata"):
                preferences.update(m["metadata"])
            else:
                # 尝试解析内容
                preferences[m["content"]] = True

        return preferences

    def get_recent_recommendations(self, limit: int = 5) -> List[str]:
        """获取最近的投资建议"""
        memories = self.get_memories(memory_type="recommendation", limit=limit)
        return [m["content"] for m in memories]

    def save_recommendation(self, recommendation: str, metadata: Dict = None):
        """保存投资建议"""
        self.add_memory(
            memory_type="recommendation",
            content=recommendation,
            metadata=metadata or {"timestamp": datetime.now().isoformat()},
            importance=3,
        )

    def save_preference(self, preference_key: str, preference_value: Any):
        """保存用户偏好"""
        self.add_memory(
            memory_type="preference",
            content=f"{preference_key}: {preference_value}",
            metadata={preference_key: preference_value},
            importance=4,
        )

    def save_insight(self, insight: str, importance: int = 2):
        """保存洞察"""
        self.add_memory(
            memory_type="insight",
            content=insight,
            importance=importance,
        )

    def get_context_for_agent(self) -> str:
        """
        获取给 Agent 的上下文信息
        包括用户偏好和最近的建议
        """
        context_parts = []

        # 用户偏好
        preferences = self.get_user_preferences()
        if preferences:
            pref_str = ", ".join([f"{k}: {v}" for k, v in preferences.items()])
            context_parts.append(f"【用户偏好】{pref_str}")

        # 最近的建议
        recent = self.get_recent_recommendations(limit=3)
        if recent:
            context_parts.append(f"【历史建议摘要】{'; '.join([r[:50] + '...' for r in recent])}")

        return "\n".join(context_parts) if context_parts else ""
