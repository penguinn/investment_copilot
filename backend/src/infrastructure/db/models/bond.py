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


class Bond(Base):
    """债券基础信息表"""

    __tablename__ = "bonds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True, comment="债券代码")
    name = Column(String(200), nullable=False, comment="债券名称")
    bond_type = Column(String(50), comment="债券类型(treasury/corporate/convertible)")
    issuer = Column(String(200), comment="发行人")
    rating = Column(String(10), comment="信用评级")
    coupon_rate = Column(Float, comment="票面利率")
    maturity_date = Column(DateTime, comment="到期日")
    issue_date = Column(DateTime, comment="发行日期")
    issue_amount = Column(Float, comment="发行规模(亿)")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_bonds_type", "bond_type"),
        Index("ix_bonds_rating", "rating"),
    )


class BondQuote(Base):
    """债券行情时序表"""

    __tablename__ = "bond_quotes"

    time = Column(DateTime, primary_key=True, comment="时间")
    code = Column(String(20), primary_key=True, comment="债券代码")
    name = Column(String(200), comment="债券名称")
    bond_type = Column(String(50), comment="债券类型")
    price = Column(Float, comment="最新价")
    open = Column(Float, comment="开盘价")
    high = Column(Float, comment="最高价")
    low = Column(Float, comment="最低价")
    close = Column(Float, comment="收盘价")
    change = Column(Float, comment="涨跌额")
    change_percent = Column(Float, comment="涨跌幅")
    ytm = Column(Float, comment="到期收益率")
    volume = Column(Float, comment="成交量")
    amount = Column(Float, comment="成交额")
    # 可转债特有字段
    convert_premium = Column(Float, comment="转股溢价率")
    convert_value = Column(Float, comment="转股价值")

    __table_args__ = (
        Index("ix_bond_quotes_code_time", "code", "time"),
        Index("ix_bond_quotes_type_time", "bond_type", "time"),
        {"comment": "债券行情时序表 - TimescaleDB hypertable"},
    )


class BondWatchlist(Base):
    """债券自选表"""

    __tablename__ = "bond_watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, default="default", comment="用户ID")
    code = Column(String(20), nullable=False, comment="债券代码")
    name = Column(String(200), comment="债券名称")
    bond_type = Column(String(50), comment="债券类型")
    sort_order = Column(Integer, default=0, comment="排序")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_bond_watchlist_user", "user_id"),
        Index("ix_bond_watchlist_user_code", "user_id", "code", unique=True),
    )


class TreasuryYield(Base):
    """国债收益率时序表"""

    __tablename__ = "treasury_yields"

    time = Column(DateTime, primary_key=True, comment="时间")
    country = Column(String(10), primary_key=True, default="CN", comment="国家")
    term = Column(String(20), primary_key=True, comment="期限(1Y/2Y/5Y/10Y/30Y)")
    yield_rate = Column(Float, comment="收益率")
    change = Column(Float, comment="变动(bp)")
    prev_yield = Column(Float, comment="前值")

    __table_args__ = (
        Index("ix_treasury_yields_country_time", "country", "time"),
        {"comment": "国债收益率时序表 - TimescaleDB hypertable"},
    )
