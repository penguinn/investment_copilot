from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)

from src.infrastructure.db.database import Base


class Fund(Base):
    """基金基础信息表"""

    __tablename__ = "funds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True, comment="基金代码")
    name = Column(String(200), nullable=False, comment="基金名称")
    full_name = Column(String(500), comment="基金全称")
    fund_type = Column(String(50), comment="基金类型(股票型/混合型/债券型/指数型/货币型/QDII)")
    manager = Column(String(100), comment="基金经理")
    company = Column(String(200), comment="基金公司")
    establish_date = Column(DateTime, comment="成立日期")
    asset_size = Column(Float, comment="资产规模(亿)")
    is_active = Column(Boolean, default=True, comment="是否活跃")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_funds_type", "fund_type"),
    )


class FundNav(Base):
    """基金净值时序表"""

    __tablename__ = "fund_navs"

    time = Column(DateTime, primary_key=True, comment="时间")
    code = Column(String(20), primary_key=True, comment="基金代码")
    name = Column(String(200), comment="基金名称")
    fund_type = Column(String(50), comment="基金类型")
    nav = Column(Float, comment="单位净值")
    acc_nav = Column(Float, comment="累计净值")
    change = Column(Float, comment="日涨跌")
    change_percent = Column(Float, comment="日涨跌幅")
    return_1w = Column(Float, comment="近1周收益")
    return_1m = Column(Float, comment="近1月收益")
    return_3m = Column(Float, comment="近3月收益")
    return_6m = Column(Float, comment="近6月收益")
    return_1y = Column(Float, comment="近1年收益")
    return_ytd = Column(Float, comment="今年以来收益")

    __table_args__ = (
        Index("ix_fund_navs_code_time", "code", "time"),
        Index("ix_fund_navs_type_time", "fund_type", "time"),
        {"comment": "基金净值时序表 - TimescaleDB hypertable"},
    )


class FundWatchlist(Base):
    """基金自选表"""

    __tablename__ = "fund_watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, default="default", comment="用户ID")
    code = Column(String(20), nullable=False, comment="基金代码")
    name = Column(String(200), comment="基金名称")
    fund_type = Column(String(50), comment="基金类型")
    sort_order = Column(Integer, default=0, comment="排序")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_fund_watchlist_user", "user_id"),
        Index("ix_fund_watchlist_user_code", "user_id", "code", unique=True),
    )
