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

    # ========== 场外基金排行榜和详情 ==========

    async def get_fund_ranking(
        self,
        fund_type: str = None,
        sort_by: str = "return_1y",
        limit: int = 20,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """获取基金排行榜"""
        cache_key = self._cache_key("ranking", fund_type or "all", sort_by, str(limit))

        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        data = self.client.get_fund_ranking(fund_type, sort_by, limit)

        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_DAILY)

        return data

    async def get_fund_detail_full(self, code: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """获取基金完整详情"""
        cache_key = self._cache_key("detail_full", code)

        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        data = self.client.get_fund_detail(code)

        if data:
            # 获取历史净值走势
            history = self.client.get_fund_history(code)
            if history:
                data["history"] = history[-90:]  # 最近 90 天

            await self._set_to_cache(cache_key, data, CACHE_TTL_DAILY)

        return data

    async def search_otc_fund(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索场外基金（使用缓存的完整列表）"""
        cache_key = self._cache_key("search_otc", keyword)

        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        data = self.client.search_otc_fund(keyword)

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

    # ========== 场外基金自选相关 ==========

    async def get_otc_watchlist(
        self,
        user_id: str = "default",
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """获取场外基金自选列表"""
        cache_key = self._cache_key("otc_watchlist", user_id)

        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        watchlist = await self.watchlist_repo.get_by_user(user_id)

        if not watchlist:
            return []

        # 过滤出场外基金（market 字段为 OTC 或空）
        otc_items = [item for item in watchlist if getattr(item, 'market', 'OTC') in ['OTC', None, '']]

        if not otc_items:
            return []

        # 从缓存的完整列表中获取数据
        all_funds = self.client._get_otc_fund_list_cached()
        fund_map = {f["code"]: f for f in all_funds}

        # 获取历史走势
        history_map = {}
        for item in otc_items:
            try:
                history = self.client.get_fund_history(item.code)
                if history:
                    history_map[item.code] = [h["nav"] for h in history[-30:]]
            except Exception as e:
                logger.debug(f"Failed to get fund history for {item.code}: {e}")

        result = []
        for item in otc_items:
            fund = fund_map.get(item.code, {})
            history_data = history_map.get(item.code, [])
            result.append({
                "code": item.code,
                "name": item.name or fund.get("name", ""),
                "fund_type": item.fund_type or fund.get("fund_type", ""),
                "nav": fund.get("nav", 0),
                "acc_nav": fund.get("acc_nav", 0),
                "change_percent": fund.get("change_percent", 0),
                "return_1w": fund.get("return_1w", 0),
                "return_1m": fund.get("return_1m", 0),
                "return_3m": fund.get("return_3m", 0),
                "return_6m": fund.get("return_6m", 0),
                "return_1y": fund.get("return_1y", 0),
                "return_ytd": fund.get("return_ytd", 0),
                "history_data": history_data,
                "sort_order": item.sort_order,
                "notes": item.notes,
            })

        await self._set_to_cache(cache_key, result, CACHE_TTL_REALTIME)
        return result

    async def add_otc_to_watchlist(
        self,
        code: str,
        user_id: str = "default",
        name: str = None,
        fund_type: str = None,
    ) -> Dict[str, Any]:
        """添加场外基金到自选"""
        item = await self.watchlist_repo.add_to_watchlist(
            user_id=user_id,
            code=code,
            name=name,
            fund_type=fund_type,
            market="OTC",
        )

        # 清除缓存
        await self._delete_from_cache(self._cache_key("otc_watchlist", user_id))

        return {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "fund_type": item.fund_type,
        }

    async def remove_otc_from_watchlist(
        self,
        code: str,
        user_id: str = "default",
    ) -> bool:
        """从场外基金自选移除"""
        result = await self.watchlist_repo.remove_from_watchlist(user_id, code)
        await self._delete_from_cache(self._cache_key("otc_watchlist", user_id))
        return result

    async def sync_otc_watchlist_data(self, user_id: str = "default") -> None:
        """同步场外基金自选数据（后台任务调用）"""
        try:
            watchlist = await self.watchlist_repo.get_by_user(user_id)

            # 过滤出场外基金
            otc_items = [item for item in watchlist if getattr(item, 'market', 'OTC') in ['OTC', None, '']]

            if not otc_items:
                return

            # 从缓存的完整列表中获取数据
            all_funds = self.client._get_otc_fund_list_cached()
            fund_map = {f["code"]: f for f in all_funds}

            # 获取历史走势
            history_map = {}
            for item in otc_items:
                try:
                    history = self.client.get_fund_history(item.code)
                    if history:
                        history_map[item.code] = [h["nav"] for h in history[-30:]]
                except Exception as e:
                    logger.debug(f"Failed to get fund history for {item.code}: {e}")

            result = []
            for item in otc_items:
                fund = fund_map.get(item.code, {})
                history_data = history_map.get(item.code, [])
                result.append({
                    "code": item.code,
                    "name": item.name or fund.get("name", ""),
                    "fund_type": item.fund_type or fund.get("fund_type", ""),
                    "nav": fund.get("nav", 0),
                    "acc_nav": fund.get("acc_nav", 0),
                    "change_percent": fund.get("change_percent", 0),
                    "return_1w": fund.get("return_1w", 0),
                    "return_1m": fund.get("return_1m", 0),
                    "return_3m": fund.get("return_3m", 0),
                    "return_6m": fund.get("return_6m", 0),
                    "return_1y": fund.get("return_1y", 0),
                    "return_ytd": fund.get("return_ytd", 0),
                    "history_data": history_data,
                    "sort_order": item.sort_order,
                    "notes": item.notes,
                })

            # 写入缓存
            cache_key = self._cache_key("otc_watchlist", user_id)
            await self._set_to_cache(cache_key, result, CACHE_TTL_REALTIME)

            logger.debug(f"Synced OTC watchlist for user {user_id}: {len(result)} items")

        except Exception as e:
            logger.warning(f"Failed to sync OTC watchlist for {user_id}: {e}")

    # ==================== 场内基金（ETF）相关方法 ====================

    async def get_etf_realtime(
        self,
        codes: List[str] = None,
        etf_type: str = None,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """获取 ETF 实时行情"""
        cache_key = self._cache_key(
            "etf_realtime",
            ",".join(codes) if codes else "all",
            etf_type or "all",
        )

        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        data = self.client.get_etf_realtime(codes)

        # 按类型过滤
        if etf_type and etf_type != "全部":
            data = [d for d in data if d.get("etf_type") == etf_type]

        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_REALTIME)

        return data

    async def get_etf_history(
        self,
        code: str,
        days: int = 30,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """获取 ETF 历史数据"""
        cache_key = self._cache_key("etf_history", code, str(days))

        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        data = self.client.get_etf_history(code, days=days)

        if data:
            # ETF 历史数据缓存 1 小时
            await self._set_to_cache(cache_key, data, 3600)

        return data

    async def search_etf(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索 ETF"""
        cache_key = self._cache_key("etf_search", keyword)

        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        data = self.client.search_etf(keyword)

        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_DAILY)

        return data

    async def get_hot_etfs(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """获取热门 ETF"""
        cache_key = self._cache_key("hot_etfs")

        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        data = self.client.get_hot_etfs()

        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_REALTIME)

        return data

    # ========== ETF 自选相关 ==========

    async def get_etf_watchlist(
        self,
        user_id: str = "default",
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """获取 ETF 自选列表"""
        cache_key = self._cache_key("etf_watchlist", user_id)

        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        watchlist = await self.watchlist_repo.get_by_user(user_id)

        if not watchlist:
            return []

        # 过滤出 ETF（market 字段为 ETF 的）
        etf_items = [item for item in watchlist if getattr(item, 'market', None) == 'ETF']

        if not etf_items:
            return []

        codes = [item.code for item in etf_items]
        etf_data = self.client.get_etf_realtime(codes)
        etf_map = {e["code"]: e for e in etf_data}

        # 获取走势数据
        history_map = {}
        for code in codes:
            try:
                history = self.client.get_etf_history(code, days=7)
                if history:
                    history_map[code] = [h["close"] for h in history]
            except Exception as e:
                logger.debug(f"Failed to get ETF history for {code}: {e}")

        result = []
        for item in etf_items:
            etf = etf_map.get(item.code, {})
            history_data = history_map.get(item.code, [])
            result.append({
                "code": item.code,
                "name": item.name or etf.get("name", ""),
                "etf_type": etf.get("etf_type", ""),
                "price": etf.get("price", 0),
                "change": etf.get("change", 0),
                "change_percent": etf.get("change_percent", 0),
                "open": etf.get("open", 0),
                "high": etf.get("high", 0),
                "low": etf.get("low", 0),
                "volume": etf.get("volume", 0),
                "amount": etf.get("amount", 0),
                "history_data": history_data,
                "sort_order": item.sort_order,
                "notes": item.notes,
            })

        await self._set_to_cache(cache_key, result, CACHE_TTL_REALTIME)
        return result

    async def add_etf_to_watchlist(
        self,
        code: str,
        user_id: str = "default",
        name: str = None,
    ) -> Dict[str, Any]:
        """添加 ETF 到自选"""
        item = await self.watchlist_repo.add_to_watchlist(
            user_id=user_id,
            code=code,
            name=name,
            market="ETF",  # 使用 market 字段区分 ETF
        )

        # 清除缓存
        await self._delete_from_cache(self._cache_key("etf_watchlist", user_id))

        return {
            "id": item.id,
            "code": item.code,
            "name": item.name,
        }

    async def remove_etf_from_watchlist(
        self,
        code: str,
        user_id: str = "default",
    ) -> bool:
        """从 ETF 自选移除"""
        result = await self.watchlist_repo.remove_from_watchlist(user_id, code)
        await self._delete_from_cache(self._cache_key("etf_watchlist", user_id))
        return result

    async def sync_etf_watchlist_data(self, user_id: str = "default") -> None:
        """同步 ETF 自选数据（后台任务调用）"""
        try:
            watchlist = await self.watchlist_repo.get_by_user(user_id)

            # 过滤出 ETF
            etf_items = [item for item in watchlist if getattr(item, 'market', None) == 'ETF']

            if not etf_items:
                return

            codes = [item.code for item in etf_items]

            # 获取实时数据
            etf_data = self.client.get_etf_realtime(codes)
            etf_map = {e["code"]: e for e in etf_data}

            # 获取走势数据
            history_map = {}
            for code in codes:
                try:
                    history = self.client.get_etf_history(code, days=7)
                    if history:
                        history_map[code] = [h["close"] for h in history]
                except Exception as e:
                    logger.debug(f"Failed to get ETF history for {code}: {e}")

            # 构建结果
            result = []
            for item in etf_items:
                etf = etf_map.get(item.code, {})
                history_data = history_map.get(item.code, [])
                result.append({
                    "code": item.code,
                    "name": item.name or etf.get("name", ""),
                    "etf_type": etf.get("etf_type", ""),
                    "price": etf.get("price", 0),
                    "change": etf.get("change", 0),
                    "change_percent": etf.get("change_percent", 0),
                    "open": etf.get("open", 0),
                    "high": etf.get("high", 0),
                    "low": etf.get("low", 0),
                    "volume": etf.get("volume", 0),
                    "amount": etf.get("amount", 0),
                    "history_data": history_data,
                    "sort_order": item.sort_order,
                    "notes": item.notes,
                })

            # 写入缓存
            cache_key = self._cache_key("etf_watchlist", user_id)
            await self._set_to_cache(cache_key, result, CACHE_TTL_REALTIME)

            logger.debug(f"Synced ETF watchlist for user {user_id}: {len(result)} items")

        except Exception as e:
            logger.warning(f"Failed to sync ETF watchlist for {user_id}: {e}")
