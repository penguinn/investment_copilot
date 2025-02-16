from datetime import datetime
from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from django.db import transaction
from django.db.models import Avg, Max, Min

from ....api.model.gold import GoldIndex
from .repository import BaseTimeSeriesRepository


class GoldRepository(BaseTimeSeriesRepository):
    """黄金数据仓储"""

    def __init__(self):
        super().__init__(GoldIndex)

    @sync_to_async
    @transaction.atomic
    def save(self, data: Dict[str, Any]) -> None:
        """保存黄金数据"""
        self.model.objects.create(
            symbol=data["symbol"],
            name=data["name"],
            time=datetime.now(),
            price=data["price"],
            open=data["price"],  # 当前只能获取实时价格
            high=data["price"],
            low=data["price"],
            close=data["price"],
            change=data["change"],
            change_percent=data["change_percent"],
        )

    @sync_to_async
    def get_latest(self, symbol: str) -> Optional[GoldIndex]:
        """获取最新黄金数据"""
        return self.model.objects.filter(symbol=symbol).order_by("-time").first()

    @sync_to_async
    def get_history(
        self, start_time: str, end_time: str, symbol: str
    ) -> List[GoldIndex]:
        """获取历史数据"""
        return list(
            self.model.objects.filter(
                symbol=symbol, time__range=(start_time, end_time)
            ).order_by("time")
        )

    @sync_to_async
    def get_by_time_bucket(
        self, start_time: str, end_time: str, interval: str, symbol: str
    ) -> List[Dict[str, Any]]:
        """获取时间段内的聚合数据"""
        return list(
            self.model.objects.filter(symbol=symbol, time__range=(start_time, end_time))
            .time_bucket("time", interval)
            .annotate(
                avg_price=Avg("price"), max_price=Max("high"), min_price=Min("low")
            )
            .order_by("time_bucket")
        )
