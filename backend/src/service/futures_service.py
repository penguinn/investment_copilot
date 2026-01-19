"""
期货服务
"""
import logging
from typing import Any, Dict, List, Optional

from src.service.base import BaseService
from src.config import CACHE_TTL_REALTIME, CACHE_TTL_DAILY
from src.infrastructure.client.akshare.futures import FuturesClient
from src.infrastructure.db.models.futures import Futures, FuturesQuote, FuturesWatchlist
from src.infrastructure.db.repository.base import TimeSeriesRepository, WatchlistRepository

logger = logging.getLogger(__name__)


class FuturesService(BaseService):
    """期货服务"""

    def __init__(self):
        super().__init__("futures")
        self.client = FuturesClient()
        self.quote_repo = TimeSeriesRepository(FuturesQuote)
        self.watchlist_repo = WatchlistRepository(FuturesWatchlist)

    async def get_realtime_quotes(
        self,
        category: str = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取期货实时行情
        :param category: 分类 (index/bond/commodity)
        """
        cache_key = self._cache_key("realtime", category or "all")
        
        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        data = self.client.get_futures_realtime(category)
        
        if data:
            try:
                await self.quote_repo.save_quotes(data)
            except Exception as e:
                logger.warning(f"Failed to save futures quotes: {e}")
            
            # 始终写入缓存
            await self._set_to_cache(cache_key, data, CACHE_TTL_REALTIME)
        
        return data

    async def get_main_contracts(self) -> List[Dict[str, Any]]:
        """获取主力合约列表"""
        cache_key = self._cache_key("main_contracts")
        
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        data = self.client.get_main_contracts()
        
        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_DAILY)
        
        return data

    async def get_futures_detail(self, code: str) -> Optional[Dict[str, Any]]:
        """获取期货合约详情"""
        data = await self.get_realtime_quotes()
        for item in data:
            if item["code"] == code:
                return item
        return None

    async def get_futures_history(
        self,
        code: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """获取期货历史数据"""
        cache_key = self._cache_key("history", code, start_date, end_date)
        
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        data = self.client.get_futures_history(code, start_date, end_date)
        
        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_DAILY)
        
        return data

    # ========== 自选相关 ==========
    
    async def get_watchlist(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """获取自选期货列表"""
        cache_key = self._cache_key("watchlist", user_id)
        
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        watchlist = await self.watchlist_repo.get_by_user(user_id)
        
        if not watchlist:
            return []

        quotes = await self.get_realtime_quotes()
        quote_map = {q["code"]: q for q in quotes}
        
        result = []
        for item in watchlist:
            quote = quote_map.get(item.code, {})
            result.append({
                "code": item.code,
                "name": item.name or quote.get("name", ""),
                "category": item.category or quote.get("category", ""),
                "sort_order": item.sort_order,
                "notes": item.notes,
                **{k: v for k, v in quote.items() if k not in ["code", "name", "category"]},
            })
        
        await self._set_to_cache(cache_key, result, CACHE_TTL_REALTIME)
        return result

    async def add_to_watchlist(
        self,
        code: str,
        user_id: str = "default",
        name: str = None,
        category: str = None
    ) -> Dict[str, Any]:
        """添加到自选"""
        item = await self.watchlist_repo.add_to_watchlist(
            user_id=user_id,
            code=code,
            name=name,
            category=category
        )
        
        await self._delete_from_cache(self._cache_key("watchlist", user_id))
        
        return {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "category": item.category,
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
