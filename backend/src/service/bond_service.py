"""
债券服务
"""
import logging
from typing import Any, Dict, List, Optional

from src.service.base import BaseService
from src.config import CACHE_TTL_REALTIME, CACHE_TTL_DAILY
from src.infrastructure.client.akshare.bond import BondClient
from src.infrastructure.db.models.bond import Bond, BondQuote, BondWatchlist, TreasuryYield
from src.infrastructure.db.repository.base import TimeSeriesRepository, WatchlistRepository

logger = logging.getLogger(__name__)


class BondService(BaseService):
    """债券服务"""

    def __init__(self):
        super().__init__("bond")
        self.client = BondClient()
        self.quote_repo = TimeSeriesRepository(BondQuote)
        self.yield_repo = TimeSeriesRepository(TreasuryYield, code_field="term")
        self.watchlist_repo = WatchlistRepository(BondWatchlist)

    async def get_treasury_yields(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """获取国债收益率"""
        cache_key = self._cache_key("treasury_yields")
        
        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        data = self.client.get_treasury_yield()
        
        if data:
            try:
                await self.yield_repo.save_quotes(data)
            except Exception as e:
                logger.warning(f"Failed to save treasury yields: {e}")
            
            await self._set_to_cache(cache_key, data, CACHE_TTL_REALTIME)
        
        return data

    async def get_realtime_quotes(
        self,
        bond_type: str = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取债券实时行情
        :param bond_type: 债券类型 (treasury/corporate/convertible)
        """
        cache_key = self._cache_key("realtime", bond_type or "all")
        
        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        data = self.client.get_bond_realtime(bond_type)
        
        if data:
            try:
                await self.quote_repo.save_quotes(data)
            except Exception as e:
                logger.warning(f"Failed to save bond quotes: {e}")
            
            await self._set_to_cache(cache_key, data, CACHE_TTL_REALTIME)
        
        return data

    async def get_bond_detail(self, code: str) -> Optional[Dict[str, Any]]:
        """获取债券详情"""
        data = await self.get_realtime_quotes()
        for item in data:
            if item["code"] == code:
                return item
        return None

    async def search_bond(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索债券"""
        cache_key = self._cache_key("search", keyword)
        
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        data = self.client.search_bond(keyword)
        
        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_DAILY)
        
        return data

    # ========== 自选相关 ==========
    
    async def get_watchlist(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """获取自选债券列表"""
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
                "bond_type": item.bond_type or quote.get("bond_type", ""),
                "sort_order": item.sort_order,
                "notes": item.notes,
                **{k: v for k, v in quote.items() if k not in ["code", "name", "bond_type"]},
            })
        
        await self._set_to_cache(cache_key, result, CACHE_TTL_REALTIME)
        return result

    async def add_to_watchlist(
        self,
        code: str,
        user_id: str = "default",
        name: str = None,
        bond_type: str = None
    ) -> Dict[str, Any]:
        """添加到自选"""
        item = await self.watchlist_repo.add_to_watchlist(
            user_id=user_id,
            code=code,
            name=name,
            bond_type=bond_type
        )
        
        await self._delete_from_cache(self._cache_key("watchlist", user_id))
        
        return {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "bond_type": item.bond_type,
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
