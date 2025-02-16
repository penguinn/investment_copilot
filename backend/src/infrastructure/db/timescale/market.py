from datetime import datetime
from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from django.db import transaction
from django.db.models import Avg, Max, Min, Sum

from ....api.model.market import MarketIndex
from .repository import BaseTimeSeriesRepository


class MarketRepository(BaseTimeSeriesRepository):
    """市场数据仓储"""

    def __init__(self):
        super().__init__(MarketIndex)

    @sync_to_async
    @transaction.atomic
    def save(self, data: Dict[str, Any]) -> None:
        """保存市场数据"""
        self.model.objects.create(
            symbol=data["symbol"],
            market=data["market"],
            name=data["name"],
            time=datetime.strptime(data["time"], "%Y-%m-%d %H:%M:%S"),
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            volume=data["volume"],
        )

    @sync_to_async
    def get_latest(self, market: str, symbol: str) -> Optional[MarketIndex]:
        """获取最新市场数据"""
        return (
            self.model.objects.filter(market=market, symbol=symbol)
            .order_by("-time")
            .first()
        )

    @sync_to_async
    def get_history(
        self, start_time: str, end_time: str, market: str, symbol: str
    ) -> List[MarketIndex]:
        """获取历史数据"""
        return list(
            self.model.objects.filter(
                market=market, symbol=symbol, time__range=(start_time, end_time)
            ).order_by("time")
        )

    @sync_to_async
    def get_by_time_bucket(
        self, start_time: str, end_time: str, interval: str, market: str, symbol: str
    ) -> List[Dict[str, Any]]:
        """获取时间段内的聚合数据"""
        return list(
            self.model.objects.filter(
                market=market, symbol=symbol, time__range=(start_time, end_time)
            )
            .time_bucket("time", interval)
            .annotate(
                avg_price=Avg("close"),
                max_price=Max("high"),
                min_price=Min("low"),
                volume_sum=Sum("volume"),
            )
            .order_by("time_bucket")
        )
