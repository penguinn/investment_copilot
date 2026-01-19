"""
基金服务
"""
import logging
from typing import Any, Dict, List, Optional

from src.service.base import BaseService
from src.config import CACHE_TTL_REALTIME, CACHE_TTL_DAILY
from src.infrastructure.client.akshare.fund import FundClient
from src.infrastructure.db.models.fund import Fund, FundNav, FundWatchlist
from src.infrastructure.db.repository.base import TimeSeriesRepository, WatchlistRepository

logger = logging.getLogger(__name__)


class FundService(BaseService):
    """基金服务"""

    def __init__(self):
        super().__init__("fund")
        self.client = FundClient()
        self.nav_repo = TimeSeriesRepository(FundNav)
        self.watchlist_repo = WatchlistRepository(FundWatchlist)

    async def get_realtime_navs(
        self,
        codes: List[str] = None,
        fund_type: str = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """获取基金实时净值"""
        cache_key = self._cache_key(
            "realtime",
            ",".join(codes) if codes else "all",
            fund_type or "all"
        )
        
        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        data = self.client.get_fund_realtime(codes)
        
        # 过滤类型
        if fund_type:
            data = [d for d in data if d.get("fund_type") == fund_type]
        
        if data:
            try:
                await self.nav_repo.save_quotes(data)
            except Exception as e:
                logger.warning(f"Failed to save fund navs: {e}")
            
            # 始终写入缓存
            await self._set_to_cache(cache_key, data, CACHE_TTL_REALTIME)
        
        return data

    async def get_fund_type_summary(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """获取各类型基金的汇总统计数据"""
        cache_key = self._cache_key("type_summary")
        
        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        data = self.client.get_fund_type_summary()
        
        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_REALTIME)
        
        return data

    async def get_fund_detail(self, code: str) -> Optional[Dict[str, Any]]:
        """获取基金详情"""
        cache_key = self._cache_key("detail", code)
        
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        data = self.client.get_fund_realtime([code])
        if data:
            result = data[0]
            await self._set_to_cache(cache_key, result, CACHE_TTL_REALTIME)
            return result
        
        return None

    async def get_fund_history(self, code: str) -> List[Dict[str, Any]]:
        """获取基金历史净值"""
        cache_key = self._cache_key("history", code)
        
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        data = self.client.get_fund_history(code)
        
        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_DAILY)
        
        return data

    async def search_fund(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索基金"""
        cache_key = self._cache_key("search", keyword)
        
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        data = self.client.search_fund(keyword)
        
        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_DAILY)
        
        return data

    # ========== 自选相关 ==========
    
    async def get_watchlist(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """获取自选基金列表"""
        cache_key = self._cache_key("watchlist", user_id)
        
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        watchlist = await self.watchlist_repo.get_by_user(user_id)
        
        if not watchlist:
            return []

        codes = [item.code for item in watchlist]
        navs = self.client.get_fund_realtime(codes)
        
        nav_map = {n["code"]: n for n in navs}
        result = []
        for item in watchlist:
            nav = nav_map.get(item.code, {})
            result.append({
                "code": item.code,
                "name": item.name or nav.get("name", ""),
                "fund_type": item.fund_type or nav.get("fund_type", ""),
                "sort_order": item.sort_order,
                "notes": item.notes,
                **{k: v for k, v in nav.items() if k not in ["code", "name", "fund_type"]},
            })
        
        await self._set_to_cache(cache_key, result, CACHE_TTL_REALTIME)
        return result

    async def add_to_watchlist(
        self,
        code: str,
        user_id: str = "default",
        name: str = None,
        fund_type: str = None
    ) -> Dict[str, Any]:
        """添加到自选"""
        item = await self.watchlist_repo.add_to_watchlist(
            user_id=user_id,
            code=code,
            name=name,
            fund_type=fund_type
        )
        
        await self._delete_from_cache(self._cache_key("watchlist", user_id))
        
        return {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "fund_type": item.fund_type,
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
