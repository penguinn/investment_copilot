"""
黄金服务
"""
import logging
from typing import Any, Dict, List, Optional

from src.service.base import BaseService
from src.config import CACHE_TTL_REALTIME, CACHE_TTL_DAILY
from src.infrastructure.client.akshare.gold import GoldClient
from src.infrastructure.db.models.gold import Gold, GoldPrice, GoldWatchlist
from src.infrastructure.db.repository.base import TimeSeriesRepository, WatchlistRepository

logger = logging.getLogger(__name__)


class GoldService(BaseService):
    """黄金服务"""

    def __init__(self):
        super().__init__("gold")
        self.client = GoldClient()
        self.price_repo = TimeSeriesRepository(GoldPrice)
        self.watchlist_repo = WatchlistRepository(GoldWatchlist)

    async def get_realtime_prices(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """获取黄金实时行情"""
        cache_key = self._cache_key("realtime")
        
        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        data = self.client.get_gold_realtime()
        
        if data:
            try:
                await self.price_repo.save_quotes(data)
            except Exception as e:
                logger.warning(f"Failed to save gold prices: {e}")
            
            # 始终写入缓存
            await self._set_to_cache(cache_key, data, CACHE_TTL_REALTIME)
        
        return data

    async def get_gold_detail(self, code: str) -> Optional[Dict[str, Any]]:
        """获取黄金品种详情"""
        data = await self.get_realtime_prices()
        for item in data:
            if item["code"] == code:
                return item
        return None

    async def get_gold_history(
        self,
        code: str = "AU9999",
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """获取黄金历史数据"""
        cache_key = self._cache_key("history", code, start_date, end_date)
        
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        data = self.client.get_gold_history(code, start_date, end_date)
        
        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_DAILY)
        
        return data

    # ========== 自选相关 ==========
    
    async def get_watchlist(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """获取自选黄金列表"""
        cache_key = self._cache_key("watchlist", user_id)
        
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        watchlist = await self.watchlist_repo.get_by_user(user_id)
        
        if not watchlist:
            return []

        prices = await self.get_realtime_prices()
        price_map = {p["code"]: p for p in prices}
        
        result = []
        for item in watchlist:
            price = price_map.get(item.code, {})
            result.append({
                "code": item.code,
                "name": item.name or price.get("name", ""),
                "sort_order": item.sort_order,
                "notes": item.notes,
                **{k: v for k, v in price.items() if k not in ["code", "name"]},
            })
        
        await self._set_to_cache(cache_key, result, CACHE_TTL_REALTIME)
        return result

    async def add_to_watchlist(
        self,
        code: str,
        user_id: str = "default",
        name: str = None
    ) -> Dict[str, Any]:
        """添加到自选"""
        item = await self.watchlist_repo.add_to_watchlist(
            user_id=user_id,
            code=code,
            name=name
        )
        
        await self._delete_from_cache(self._cache_key("watchlist", user_id))
        
        return {
            "id": item.id,
            "code": item.code,
            "name": item.name,
        }

    async def remove_from_watchlist(
        self,
        code: str,
        user_id: str = "default"
    ) -> bool:
        """从自选移除"""
        result = await self.watchlist_repo.remove_from_watchlist(user_id, code)
        await self._delete_from_cache(self._cache_key("watchlist", user_id))
        return result
