"""
投资建议数据模型
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, Index

from src.infrastructure.db.database import Base


class InvestmentAdvice(Base):
    """每日投资建议表"""

    __tablename__ = "investment_advices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(20), nullable=False, comment="日期 (YYYY-MM-DD)")
    title = Column(String(200), comment="标题")
    content = Column(Text, comment="建议内容（完整版）")
    summary = Column(Text, comment="摘要（推荐列表）")
    status = Column(String(20), default="active", comment="状态: active/archived")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_investment_advices_date", "date"),
        Index("ix_investment_advices_status", "status"),
        {"comment": "每日投资建议表 - 存储 Agent 生成的投资建议"},
    )
