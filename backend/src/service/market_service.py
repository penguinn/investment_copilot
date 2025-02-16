import logging
from typing import Any, Dict, List

from ..infrastructure.client.akshare.market import MarketClient
from ..infrastructure.db.redis.market import MarketCache
from ..infrastructure.db.timescale.market import MarketRepository

logger = logging.getLogger(__name__)


class MarketService:
    """市场服务"""

    def __init__(self):
        self.client = MarketClient()
        self.repository = MarketRepository()
        self.cache = MarketCache()

    async def get_market_data(
        self, market: str, symbol: str, period: str, use_cache: bool = True
    ) -> Dict[str, Any]:
        """获取市场数据"""
        if use_cache:
            # 先从缓存获取
            cached_data = await self.cache.get_latest(market, symbol)
            if cached_data:
                return cached_data

        # 从API获取
        data = await self.client.request(market=market, symbol=symbol, period=period)

        # 保存到时序数据库
        await self.repository.save(data)

        # 设置缓存
        if use_cache:
            await self.cache.set_latest(market, symbol, data)

        return data

    async def get_market_history(
        self,
        market: str,
        symbol: str,
        start_time: str,
        end_time: str,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """获取历史数据"""
        if use_cache:
            # 先从缓存获取
            cached_data = await self.cache.get_history(
                market, symbol, start_time, end_time
            )
            if cached_data:
                return cached_data

        # 从时序数据库获取
        data = await self.repository.get_history(
            start_time=start_time, end_time=end_time, market=market, symbol=symbol
        )

        # 格式化数据
        formatted_data = [
            {
                "time": item.time.strftime("%Y-%m-%d %H:%M:%S"),
                "open": float(item.open),
                "high": float(item.high),
                "low": float(item.low),
                "close": float(item.close),
                "volume": float(item.volume),
            }
            for item in data
        ]

        # 设置缓存
        if use_cache:
            await self.cache.set_history(
                market, symbol, start_time, end_time, formatted_data
            )

        return formatted_data

    async def get_market_trend(
        self,
        market: str,
        symbol: str,
        start_time: str,
        end_time: str,
        interval: str,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """获取市场趋势数据"""
        # 从时序数据库获取聚合数据
        data = await self.repository.get_by_time_bucket(
            start_time=start_time,
            end_time=end_time,
            interval=interval,
            market=market,
            symbol=symbol,
        )

        # 格式化数据
        return [
            {
                "time": item.time_bucket.strftime("%Y-%m-%d %H:%M:%S"),
                "price": float(item.avg_price),
                "volume": float(item.volume_sum),
            }
            for item in data
        ]
