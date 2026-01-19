from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class GoldIndexBase(BaseModel):
    """黄金指数基础模型"""

    symbol: str = Field(..., description="指数代码")
    name: str = Field(..., description="指数名称")
    time: datetime = Field(..., description="时间")
    price: float = Field(..., description="当前价格")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    change: float = Field(..., description="涨跌额")
    change_percent: float = Field(..., description="涨跌幅")


class GoldIndex(GoldIndexBase):
    """黄金指数模型"""

    id: Optional[int] = Field(None, description="ID")

    class Config:
        orm_mode = True
