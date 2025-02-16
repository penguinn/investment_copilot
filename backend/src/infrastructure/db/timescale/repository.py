from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from django.db import models


class BaseTimeSeriesRepository(ABC):
    """时序数据仓储基类"""

    def __init__(self, model: models.Model):
        self.model = model

    @abstractmethod
    async def save(self, data: Dict[str, Any]) -> None:
        """保存数据"""
        pass

    @abstractmethod
    async def get_latest(self, **kwargs) -> Optional[models.Model]:
        """获取最新数据"""
        pass

    @abstractmethod
    async def get_history(
        self, start_time: str, end_time: str, **kwargs
    ) -> List[models.Model]:
        """获取历史数据"""
        pass

    @abstractmethod
    async def get_by_time_bucket(
        self, start_time: str, end_time: str, interval: str, **kwargs
    ) -> List[Dict[str, Any]]:
        """获取时间段内的聚合数据"""
        pass
