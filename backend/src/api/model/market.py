from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MarketIndexBase(BaseModel):
    """市场指数基础模型"""

    symbol: str = Field(..., description="指数代码")
    market: str = Field(..., description="市场代码")
    name: str = Field(..., description="指数名称")
    time: datetime = Field(..., description="时间")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")
    change: Optional[float] = Field(None, description="涨跌额")
    change_percent: Optional[float] = Field(None, description="涨跌幅")


class MarketIndex(MarketIndexBase):
    """市场指数模型"""

    id: Optional[int] = Field(None, description="ID")

    class Config:
        orm_mode = True
