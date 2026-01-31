"""
新闻数据模型
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text
from src.infrastructure.db.database import Base


class News(Base):
    """新闻表"""

    __tablename__ = "news"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 基本信息
    source = Column(
        String(50),
        nullable=False,
        comment="来源(cls/eastmoney/pbc/csrc/ndrc/stats/miit)",
    )
    source_name = Column(String(100), comment="来源名称")
    title = Column(String(500), comment="标题")
    content = Column(Text, nullable=False, comment="内容")
    summary = Column(Text, comment="AI摘要")
    url = Column(String(1000), comment="原文链接")

    # 分类信息
    category = Column(String(50), comment="分类(policy/news/data/announcement)")
    tags = Column(String(500), comment="标签，逗号分隔")
    importance = Column(Integer, default=1, comment="重要性(1-5)")

    # 投资相关
    related_sectors = Column(String(500), comment="相关板块，逗号分隔")
    sentiment = Column(String(20), comment="情感倾向(positive/negative/neutral)")

    # 时间信息
    publish_time = Column(DateTime, nullable=False, comment="发布时间")
    crawl_time = Column(DateTime, default=datetime.utcnow, comment="爬取时间")

    # 状态
    is_processed = Column(Boolean, default=False, comment="是否已处理(AI摘要)")
    is_active = Column(Boolean, default=True, comment="是否有效")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_news_source", "source"),
        Index("ix_news_category", "category"),
        Index("ix_news_publish_time", "publish_time"),
        Index("ix_news_source_publish", "source", "publish_time"),
        Index("ix_news_importance", "importance"),
    )


class NewsSource(Base):
    """新闻来源配置表"""

    __tablename__ = "news_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, comment="来源代码")
    name = Column(String(100), nullable=False, comment="来源名称")
    source_type = Column(String(50), comment="类型(api/crawler)")
    url = Column(String(500), comment="网站URL")
    api_endpoint = Column(String(500), comment="API地址")
    crawl_interval = Column(Integer, default=300, comment="爬取间隔(秒)")
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_crawl_time = Column(DateTime, comment="最后爬取时间")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_news_sources_code", "code"),
        Index("ix_news_sources_active", "is_active"),
    )
