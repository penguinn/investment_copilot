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


class Gold(Base):
    """黄金品种基础信息表"""

    __tablename__ = "golds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True, comment="品种代码")
    name = Column(String(100), nullable=False, comment="品种名称")
    exchange = Column(String(50), comment="交易所(SGE/COMEX/LBMA)")
    unit = Column(String(20), comment="单位(元/克, 美元/盎司)")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GoldPrice(Base):
    """黄金价格时序表"""

    __tablename__ = "gold_prices"

    time = Column(DateTime, primary_key=True, comment="时间")
    code = Column(String(20), primary_key=True, comment="品种代码")
    name = Column(String(100), comment="品种名称")
    exchange = Column(String(50), comment="交易所")
    price = Column(Float, comment="最新价")
    open = Column(Float, comment="开盘价")
    high = Column(Float, comment="最高价")
    low = Column(Float, comment="最低价")
    close = Column(Float, comment="收盘价")
    change = Column(Float, comment="涨跌额")
    change_percent = Column(Float, comment="涨跌幅")
    volume = Column(Float, comment="成交量")
    amount = Column(Float, comment="成交额")

    __table_args__ = (
        Index("ix_gold_prices_code_time", "code", "time"),
        {"comment": "黄金价格时序表 - TimescaleDB hypertable"},
    )


class GoldWatchlist(Base):
    """黄金自选表"""

    __tablename__ = "gold_watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, default="default", comment="用户ID")
    code = Column(String(20), nullable=False, comment="品种代码")
    name = Column(String(100), comment="品种名称")
    sort_order = Column(Integer, default=0, comment="排序")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_gold_watchlist_user", "user_id"),
        Index("ix_gold_watchlist_user_code", "user_id", "code", unique=True),
    )
