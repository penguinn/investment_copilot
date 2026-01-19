from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StockQuoteBase(BaseModel):
    """股票行情基础模型"""

    symbol: str = Field(..., description="股票代码")
    time: datetime = Field(..., description="时间")
    current: float = Field(..., description="当前价格")
    change: float = Field(..., description="涨跌额")
    change_percent: float = Field(..., description="涨跌幅")


class StockQuote(StockQuoteBase):
    """股票行情模型"""

    id: Optional[int] = Field(None, description="ID")

    class Config:
        orm_mode = True
