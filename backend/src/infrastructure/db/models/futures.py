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


class Futures(Base):
    """期货品种基础信息表"""

    __tablename__ = "futures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True, comment="合约代码")
    name = Column(String(100), nullable=False, comment="合约名称")
    symbol = Column(String(20), comment="品种代码")
    category = Column(String(50), comment="分类(index/commodity/bond)")
    exchange = Column(String(20), comment="交易所(CFFEX/SHFE/DCE/CZCE)")
    contract_unit = Column(String(50), comment="合约单位")
    price_unit = Column(String(50), comment="报价单位")
    min_change = Column(Float, comment="最小变动价位")
    delivery_month = Column(String(10), comment="交割月份")
    is_main = Column(Boolean, default=False, comment="是否主力合约")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_futures_category", "category"),
        Index("ix_futures_symbol", "symbol"),
    )


class FuturesQuote(Base):
    """期货行情时序表"""

    __tablename__ = "futures_quotes"

    time = Column(DateTime, primary_key=True, comment="时间")
    code = Column(String(20), primary_key=True, comment="合约代码")
    name = Column(String(100), comment="合约名称")
    category = Column(String(50), comment="分类")
    exchange = Column(String(20), comment="交易所")
    price = Column(Float, comment="最新价")
    open = Column(Float, comment="开盘价")
    high = Column(Float, comment="最高价")
    low = Column(Float, comment="最低价")
    close = Column(Float, comment="收盘价")
    settle = Column(Float, comment="结算价")
    change = Column(Float, comment="涨跌额")
    change_percent = Column(Float, comment="涨跌幅")
    volume = Column(Float, comment="成交量")
    amount = Column(Float, comment="成交额")
    open_interest = Column(Float, comment="持仓量")
    open_interest_change = Column(Float, comment="持仓变化")

    __table_args__ = (
        Index("ix_futures_quotes_code_time", "code", "time"),
        Index("ix_futures_quotes_category_time", "category", "time"),
        {"comment": "期货行情时序表 - TimescaleDB hypertable"},
    )


class FuturesWatchlist(Base):
    """期货自选表"""

    __tablename__ = "futures_watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, default="default", comment="用户ID")
    code = Column(String(20), nullable=False, comment="合约代码")
    name = Column(String(100), comment="合约名称")
    category = Column(String(50), comment="分类")
    sort_order = Column(Integer, default=0, comment="排序")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_futures_watchlist_user", "user_id"),
        Index("ix_futures_watchlist_user_code", "user_id", "code", unique=True),
    )
