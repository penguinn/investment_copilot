"""
市场指数服务
"""

import logging
from typing import Any, Dict, List

from src.config import CACHE_TTL_DAILY, CACHE_TTL_HISTORY, CACHE_TTL_REALTIME
from src.infrastructure.client.akshare.market import MarketClient
from src.service.base import BaseService

logger = logging.getLogger(__name__)


class MarketService(BaseService):
    """市场指数服务"""

    def __init__(self):
        super().__init__("market")
        self.client = MarketClient()

    async def get_market_data(
        self, market: str, symbol: str, period: str, use_cache: bool = True
    ) -> Dict[str, Any]:
        """获取市场指数数据"""
        cache_key = self._cache_key("index", market, symbol, period)

        # 尝试从缓存获取
        if use_cache:
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                return cached_data

        # 从API获取
        data = self.client.get_market_index(market=market, symbol=symbol, period=period)

        # 始终写入缓存（无论 use_cache 是 True 还是 False）
        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_REALTIME)

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
        cache_key = self._cache_key("history", market, symbol, start_time, end_time)

        if use_cache:
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                return cached_data

        # 从 API 获取历史数据
        # TODO: 实现历史数据获取
        data = []

        if use_cache and data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_DAILY)

        return data

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
        cache_key = self._cache_key(
            "trend", market, symbol, start_time, end_time, interval
        )

        if use_cache:
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                return cached_data

        # TODO: 实现趋势数据获取
        data = []

        if use_cache and data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_DAILY)

        return data

    async def get_index_history(
        self,
        market: str,
        symbol: str,
        days: int = 30,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """获取指数历史数据（用于折线图）"""
        cache_key = self._cache_key("index_history", market, symbol, str(days))

        if use_cache:
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                return cached_data

        # 从 API 获取历史数据
        data = self.client.get_index_history(market=market, symbol=symbol, days=days)

        if data:
            # 历史数据缓存1小时，因为历史数据不会变化
            await self._set_to_cache(cache_key, data, CACHE_TTL_HISTORY)

        return data
