"""
股票服务
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.service.base import BaseService
from src.config import CACHE_TTL_REALTIME, CACHE_TTL_DAILY, CACHE_TTL_WATCHLIST
from src.infrastructure.client.akshare.stock import StockClient
from src.infrastructure.db.models.stock import Stock, StockQuote, StockWatchlist
from src.infrastructure.db.repository.base import TimeSeriesRepository, WatchlistRepository

logger = logging.getLogger(__name__)


class StockService(BaseService):
    """股票服务"""

    def __init__(self):
        super().__init__("stock")
        self.client = StockClient()
        self.quote_repo = TimeSeriesRepository(StockQuote)
        self.watchlist_repo = WatchlistRepository(StockWatchlist)

    async def get_realtime_quotes(
        self, 
        codes: List[str] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取股票实时行情
        :param codes: 股票代码列表，None 则获取全部
        :param use_cache: 是否使用缓存
        """
        cache_key = self._cache_key("realtime", ",".join(codes) if codes else "all")
        
        # 尝试从缓存获取
        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        # 从 API 获取数据
        data = self.client.get_cn_stock_realtime(codes)
        
        if data:
            # 保存到数据库
            try:
                await self.quote_repo.save_quotes(data)
            except Exception as e:
                logger.warning(f"Failed to save stock quotes: {e}")
            
            # 设置缓存
            await self._set_to_cache(cache_key, data, CACHE_TTL_REALTIME)
        
        return data

    async def get_stock_detail(self, code: str) -> Optional[Dict[str, Any]]:
        """获取股票详情"""
        cache_key = self._cache_key("detail", code)
        
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        # 获取实时数据
        data = self.client.get_cn_stock_realtime([code])
        if data:
            result = data[0]
            await self._set_to_cache(cache_key, result, CACHE_TTL_REALTIME)
            return result
        
        return None

    async def get_stock_history(
        self,
        code: str,
        period: str = "daily",
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """获取股票历史数据"""
        cache_key = self._cache_key("history", code, period, start_date, end_date)
        
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        data = self.client.get_stock_history(code, period, start_date, end_date)
        
        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_DAILY)
        
        return data

    async def search_stock(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索股票"""
        cache_key = self._cache_key("search", keyword)
        
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        data = self.client.search_stock(keyword)
        
        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_DAILY)
        
        return data

    # ========== 自选相关 ==========
    
    async def get_watchlist(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """获取自选股列表"""
        cache_key = self._cache_key("watchlist", user_id)
        
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        watchlist = await self.watchlist_repo.get_by_user(user_id)
        
        if not watchlist:
            return []

        # 获取实时行情
        codes = [item.code for item in watchlist]
        quotes = self.client.get_cn_stock_realtime(codes)
        
        # 合并数据
        quote_map = {q["code"]: q for q in quotes}
        result = []
        for item in watchlist:
            quote = quote_map.get(item.code, {})
            result.append({
                "code": item.code,
                "name": item.name or quote.get("name", ""),
                "market": item.market,
                "sort_order": item.sort_order,
                "notes": item.notes,
                **{k: v for k, v in quote.items() if k not in ["code", "name", "market"]},
            })
        
        await self._set_to_cache(cache_key, result, CACHE_TTL_REALTIME)
        return result

    async def add_to_watchlist(
        self,
        code: str,
        user_id: str = "default",
        name: str = None,
        market: str = "CN"
    ) -> Dict[str, Any]:
        """添加到自选"""
        item = await self.watchlist_repo.add_to_watchlist(
            user_id=user_id,
            code=code,
            name=name,
            market=market
        )
        
        # 清除缓存
        await self._delete_from_cache(self._cache_key("watchlist", user_id))
        
        return {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "market": item.market,
        }

    async def remove_from_watchlist(
        self,
        code: str,
        user_id: str = "default"
    ) -> bool:
        """从自选移除"""
        result = await self.watchlist_repo.remove_from_watchlist(user_id, code)
        
        # 清除缓存
        await self._delete_from_cache(self._cache_key("watchlist", user_id))
        
        return result

    async def is_in_watchlist(self, code: str, user_id: str = "default") -> bool:
        """检查是否在自选中"""
        return await self.watchlist_repo.is_in_watchlist(user_id, code)
