"""
Agent 长期记忆数据模型
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from src.infrastructure.db.database import Base


class AgentMemory(Base):
    """Agent 长期记忆表"""

    __tablename__ = "agent_memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True, comment="用户ID")
    memory_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="记忆类型(preference/recommendation/insight)",
    )
    content = Column(Text, nullable=False, comment="记忆内容")
    extra_data = Column(Text, comment="元数据(JSON)")
    importance = Column(Integer, default=1, comment="重要性(1-5)")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("ix_agent_memories_user_type", "user_id", "memory_type"),)
