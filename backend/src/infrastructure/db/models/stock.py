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
    Text,
)

from src.infrastructure.db.database import Base


class Stock(Base):
    """股票基础信息表"""

    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True, comment="股票代码")
    name = Column(String(100), nullable=False, comment="股票名称")
    market = Column(String(10), nullable=False, comment="市场(CN/HK/US)")
    exchange = Column(String(20), comment="交易所")
    industry = Column(String(50), comment="行业")
    sector = Column(String(50), comment="板块")
    list_date = Column(DateTime, comment="上市日期")
    is_active = Column(Boolean, default=True, comment="是否活跃")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_stocks_market_code", "market", "code"),
    )


class StockQuote(Base):
    """股票行情时序表"""

    __tablename__ = "stock_quotes"

    time = Column(DateTime, primary_key=True, comment="时间")
    code = Column(String(20), primary_key=True, comment="股票代码")
    market = Column(String(10), nullable=False, comment="市场")
    name = Column(String(100), comment="股票名称")
    open = Column(Float, comment="开盘价")
    high = Column(Float, comment="最高价")
    low = Column(Float, comment="最低价")
    close = Column(Float, comment="收盘价/最新价")
    volume = Column(BigInteger, comment="成交量")
    amount = Column(Float, comment="成交额")
    change = Column(Float, comment="涨跌额")
    change_percent = Column(Float, comment="涨跌幅")
    turnover = Column(Float, comment="换手率")
    pe_ratio = Column(Float, comment="市盈率")
    pb_ratio = Column(Float, comment="市净率")
    total_value = Column(Float, comment="总市值")
    circulating_value = Column(Float, comment="流通市值")

    __table_args__ = (
        Index("ix_stock_quotes_code_time", "code", "time"),
        Index("ix_stock_quotes_market_time", "market", "time"),
        {"comment": "股票行情时序表 - TimescaleDB hypertable"},
    )


class StockWatchlist(Base):
    """股票自选表"""

    __tablename__ = "stock_watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, default="default", comment="用户ID")
    code = Column(String(20), nullable=False, comment="股票代码")
    market = Column(String(10), nullable=False, comment="市场")
    name = Column(String(100), comment="股票名称")
    sort_order = Column(Integer, default=0, comment="排序")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_stock_watchlist_user", "user_id"),
        Index("ix_stock_watchlist_user_code", "user_id", "code", unique=True),
    )
