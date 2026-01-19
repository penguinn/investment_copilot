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


class Forex(Base):
    """外汇货币对基础信息表"""

    __tablename__ = "forex"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True, comment="货币对代码")
    name = Column(String(100), nullable=False, comment="货币对名称")
    base_currency = Column(String(10), comment="基准货币")
    quote_currency = Column(String(10), comment="报价货币")
    category = Column(String(50), comment="分类(major/cross/cny)")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_forex_category", "category"),
    )


class ForexQuote(Base):
    """外汇行情时序表"""

    __tablename__ = "forex_quotes"

    time = Column(DateTime, primary_key=True, comment="时间")
    code = Column(String(20), primary_key=True, comment="货币对代码")
    name = Column(String(100), comment="货币对名称")
    category = Column(String(50), comment="分类")
    price = Column(Float, comment="最新价")
    open = Column(Float, comment="开盘价")
    high = Column(Float, comment="最高价")
    low = Column(Float, comment="最低价")
    close = Column(Float, comment="收盘价")
    change = Column(Float, comment="涨跌额")
    change_percent = Column(Float, comment="涨跌幅")
    bid = Column(Float, comment="买入价")
    ask = Column(Float, comment="卖出价")
    spread = Column(Float, comment="点差")

    __table_args__ = (
        Index("ix_forex_quotes_code_time", "code", "time"),
        Index("ix_forex_quotes_category_time", "category", "time"),
        {"comment": "外汇行情时序表 - TimescaleDB hypertable"},
    )


class ForexWatchlist(Base):
    """外汇自选表"""

    __tablename__ = "forex_watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, default="default", comment="用户ID")
    code = Column(String(20), nullable=False, comment="货币对代码")
    name = Column(String(100), comment="货币对名称")
    sort_order = Column(Integer, default=0, comment="排序")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_forex_watchlist_user", "user_id"),
        Index("ix_forex_watchlist_user_code", "user_id", "code", unique=True),
    )
