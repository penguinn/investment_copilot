from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
)
from src.infrastructure.db.database import Base


class MarketIndex(Base):
    """市场指数基础信息表"""

    __tablename__ = "market_indices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(
        String(20), unique=True, nullable=False, index=True, comment="指数代码"
    )
    symbol = Column(String(20), comment="交易代码")
    name = Column(String(100), nullable=False, comment="指数名称")
    market = Column(String(10), nullable=False, comment="市场(CN/HK/US)")
    exchange = Column(String(20), comment="交易所")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("ix_market_indices_market", "market"),)


class MarketIndexQuote(Base):
    """市场指数行情时序表"""

    __tablename__ = "market_index_quotes"

    time = Column(DateTime, primary_key=True, comment="时间")
    code = Column(String(20), primary_key=True, comment="指数代码")
    market = Column(String(10), nullable=False, comment="市场")
    name = Column(String(100), comment="指数名称")
    open = Column(Float, comment="开盘价")
    high = Column(Float, comment="最高价")
    low = Column(Float, comment="最低价")
    close = Column(Float, comment="收盘价/最新价")
    volume = Column(BigInteger, comment="成交量")
    amount = Column(Float, comment="成交额")
    change = Column(Float, comment="涨跌额")
    change_percent = Column(Float, comment="涨跌幅")

    __table_args__ = (
        Index("ix_market_index_quotes_code_time", "code", "time"),
        Index("ix_market_index_quotes_market_time", "market", "time"),
        {"comment": "市场指数行情时序表 - TimescaleDB hypertable"},
    )
