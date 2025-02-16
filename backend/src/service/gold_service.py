import logging
from datetime import datetime
from typing import Any, Dict, List

import pytz

from ..infrastructure.client.akshare.gold import GoldClient
from ..infrastructure.db.redis.gold import GoldCache
from ..infrastructure.db.timescale.gold import GoldRepository

logger = logging.getLogger(__name__)


class GoldService:
    """黄金服务"""

    def __init__(self):
        self.client = GoldClient()
        self.repository = GoldRepository()
        self.cache = GoldCache()

    async def get_gold_data(
        self, gold_indices: Dict[str, Dict[str, str]], use_cache: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """获取黄金数据"""
        result = {}

        for symbol in gold_indices.keys():
            if use_cache:
                # 先从缓存获取
                cached_data = await self.cache.get_latest(symbol)
                if cached_data:
                    result[symbol] = cached_data
                    continue

        # 如果有未缓存的数据，从API获取
        if len(result) < len(gold_indices):
            api_data = await self.client.request(gold_indices=gold_indices)

            # 保存到时序数据库并更新缓存
            for symbol, data in api_data.items():
                if symbol not in result:  # 只处理未缓存的数据
                    # 为数据库保存准备带时区的datetime对象
                    db_data = data.copy()
                    db_data["time"] = datetime.strptime(
                        data["time"], "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=pytz.timezone("Asia/Shanghai"))

                    # 保存到数据库
                    await self.repository.save(db_data)

                    if use_cache:
                        # 缓存和返回使用原始数据（带字符串时间）
                        await self.cache.set_latest(symbol, data)
                    result[symbol] = data

        return result

    async def get_gold_history(
        self, symbol: str, start_time: str, end_time: str, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """获取历史数据"""
        if use_cache:
            # 先从缓存获取
            cached_data = await self.cache.get_history(symbol, start_time, end_time)
            if cached_data:
                return cached_data

        # 从时序数据库获取
        data = await self.repository.get_history(
            start_time=start_time, end_time=end_time, symbol=symbol
        )

        # 格式化数据
        formatted_data = [
            {
                "time": item.time.strftime("%Y-%m-%d %H:%M:%S"),
                "price": float(item.price),
                "open": float(item.open),
                "high": float(item.high),
                "low": float(item.low),
                "close": float(item.close),
                "change": float(item.change),
                "change_percent": float(item.change_percent),
            }
            for item in data
        ]

        # 设置缓存
        if use_cache:
            await self.cache.set_history(symbol, start_time, end_time, formatted_data)

        return formatted_data

    async def get_gold_trend(
        self, symbol: str, start_time: str, end_time: str, interval: str
    ) -> List[Dict[str, Any]]:
        """获取黄金趋势数据"""
        # 从时序数据库获取聚合数据
        data = await self.repository.get_by_time_bucket(
            start_time=start_time, end_time=end_time, interval=interval, symbol=symbol
        )

        # 格式化数据
        return [
            {
                "time": item.time_bucket.strftime("%Y-%m-%d %H:%M:%S"),
                "price": float(item.avg_price),
                "high": float(item.max_price),
                "low": float(item.min_price),
            }
            for item in data
        ]
