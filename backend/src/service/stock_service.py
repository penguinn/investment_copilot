"""
股票服务
"""

import logging
from datetime import datetime, time
from typing import Any, Dict, List, Optional

from src.config import CACHE_TTL_DAILY, CACHE_TTL_REALTIME, CACHE_TTL_WATCHLIST
from src.infrastructure.client.akshare.stock import StockClient
from src.infrastructure.db.models.stock import Stock, StockQuote, StockWatchlist
from src.infrastructure.db.repository.base import (
    TimeSeriesRepository,
    WatchlistRepository,
)
from src.service.base import BaseService

logger = logging.getLogger(__name__)

# A股交易时间
TRADING_HOURS = [
    (time(9, 15), time(11, 30)),  # 上午盘（含集合竞价）
    (time(13, 0), time(15, 0)),  # 下午盘
]


class StockService(BaseService):
    """股票服务"""

    def __init__(self):
        super().__init__("stock")
        self.client = StockClient()
        self.quote_repo = TimeSeriesRepository(StockQuote)
        self.watchlist_repo = WatchlistRepository(StockWatchlist)

    def _is_trading_time(self) -> bool:
        """判断当前是否为A股交易时间"""
        now = datetime.now()

        # 周末不交易
        if now.weekday() >= 5:  # 5=Saturday, 6=Sunday
            return False

        current_time = now.time()
        for start, end in TRADING_HOURS:
            if start <= current_time <= end:
                return True

        return False

    def _should_fetch_realtime(self) -> bool:
        """判断是否需要获取实时数据

        交易时间内：获取实时数据
        非交易时间：优先使用缓存
        """
        return self._is_trading_time()

    async def get_realtime_quotes(
        self, codes: List[str] = None, use_cache: bool = True
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
        end_date: str = None,
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

    async def search_stock(
        self, keyword: str, market: str = None
    ) -> List[Dict[str, Any]]:
        """搜索股票（支持 A股、港股、美股）"""
        cache_key = self._cache_key("search", keyword, market or "all")

        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        data = []

        if market == "CN" or market is None:
            # A股搜索
            data.extend(self.client.search_stock(keyword))

        if market == "HK" or market is None:
            # 港股搜索
            data.extend(self.client.search_hk_stock(keyword))

        if market == "US" or market is None:
            # 美股搜索
            data.extend(self.client.search_us_stock(keyword))

        if data:
            # 限制返回数量
            data = data[:20]
            await self._set_to_cache(cache_key, data, CACHE_TTL_DAILY)

        return data

    # ========== 自选相关 ==========

    async def get_watchlist(
        self, user_id: str = "default", market: str = None
    ) -> List[Dict[str, Any]]:
        """获取自选股列表

        优先从缓存获取（后台任务会定期更新缓存）
        非交易时间直接返回缓存，不重新获取
        """
        cache_key = self._cache_key("watchlist", user_id, market or "all")

        # 尝试从缓存获取
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        # 非交易时间，如果没有缓存也需要获取一次数据
        watchlist = await self.watchlist_repo.get_by_user(user_id)

        if not watchlist:
            return []

        # 按市场过滤
        if market:
            watchlist = [item for item in watchlist if item.market == market]

        if not watchlist:
            return []

        # 按市场分类
        cn_items = [item for item in watchlist if item.market == "CN"]
        hk_items = [item for item in watchlist if item.market == "HK"]
        us_items = [item for item in watchlist if item.market == "US"]

        # 获取 A股实时行情
        cn_codes = [item.code for item in cn_items]
        cn_quotes = self.client.get_stocks_realtime_batch(cn_codes) if cn_codes else []

        # 获取港股实时行情（使用历史数据获取更完整信息，包含换手率）
        hk_codes = [item.code for item in hk_items]
        hk_quotes = []
        for code in hk_codes:
            quote = self.client.get_hk_stock_realtime_with_history(code)
            if quote:
                hk_quotes.append(quote)

        # 获取美股实时行情
        us_codes = [item.code for item in us_items]
        us_quotes = self.client.get_us_stock_realtime(us_codes) if us_codes else []

        # 合并所有行情数据
        all_quotes = cn_quotes + hk_quotes + us_quotes
        quote_map = {q["code"]: q for q in all_quotes}

        # 获取走势图数据
        history_map = {}
        # A股走势
        for code in cn_codes:
            try:
                history = self.client.get_stock_history(code, period="daily")
                if history:
                    history_map[code] = [h["close"] for h in history[-7:]]
            except Exception as e:
                logger.debug(f"Failed to get CN history for {code}: {e}")

        # 港股走势
        for code in hk_codes:
            try:
                history = self.client.get_hk_stock_history(code, period="daily")
                if history:
                    history_map[code] = [h["close"] for h in history[-7:]]
            except Exception as e:
                logger.debug(f"Failed to get HK history for {code}: {e}")

        # 合并数据
        result = []
        for item in watchlist:
            quote = quote_map.get(item.code, {})
            history_data = history_map.get(item.code, [])
            result.append(self._build_watchlist_item(item, quote, history_data))

        # 非交易时间延长缓存时间
        cache_ttl = CACHE_TTL_REALTIME if self._is_trading_time() else CACHE_TTL_DAILY
        await self._set_to_cache(cache_key, result, cache_ttl)
        return result

    def _build_watchlist_item(
        self, item, quote: dict, history_data: List[float] = None
    ) -> dict:
        """构建自选股数据项（包含更丰富的信息）"""
        # 格式化市值（亿）
        total_value = quote.get("total_value", 0)
        market_cap = round(total_value / 100000000, 2) if total_value else 0

        return {
            "code": item.code,
            "name": item.name or quote.get("name", ""),
            "market": item.market,
            "sort_order": item.sort_order,
            "notes": item.notes,
            # 价格相关
            "price": quote.get("close", 0),
            "change": quote.get("change", 0),
            "change_percent": quote.get("change_percent", 0),
            # 今日行情
            "open": quote.get("open", 0),
            "high": quote.get("high", 0),
            "low": quote.get("low", 0),
            # 成交量/额
            "volume": quote.get("volume", 0),
            "amount": quote.get("amount", 0),
            # 长线跟踪指标
            "turnover": quote.get("turnover", 0),  # 换手率
            "pe_ratio": quote.get("pe_ratio", 0),  # 市盈率
            "pb_ratio": quote.get("pb_ratio", 0),  # 市净率
            "market_cap": market_cap,  # 总市值（亿）
            # 走势图数据（最近7天收盘价）
            "history_data": history_data or [],
        }

    async def sync_watchlist_data(self, user_id: str = "default") -> None:
        """同步自选股数据到缓存和数据库（供后台任务调用）"""
        # 非交易时间跳过同步（使用已有缓存）
        if not self._should_fetch_realtime():
            logger.debug("Not trading time, skip watchlist sync")
            return

        watchlist = await self.watchlist_repo.get_by_user(user_id)

        if not watchlist:
            return

        # 按市场分类
        cn_items = [item for item in watchlist if item.market == "CN"]
        hk_items = [item for item in watchlist if item.market == "HK"]
        us_items = [item for item in watchlist if item.market == "US"]

        cn_codes = [item.code for item in cn_items]
        hk_codes = [item.code for item in hk_items]
        us_codes = [item.code for item in us_items]

        if not cn_codes and not hk_codes and not us_codes:
            return

        # 获取各市场实时行情
        cn_quotes = self.client.get_stocks_realtime_batch(cn_codes) if cn_codes else []

        # 港股使用历史数据获取更完整信息（包含换手率）
        hk_quotes = []
        for code in hk_codes:
            quote = self.client.get_hk_stock_realtime_with_history(code)
            if quote:
                hk_quotes.append(quote)

        us_quotes = self.client.get_us_stock_realtime(us_codes) if us_codes else []

        all_quotes = cn_quotes + hk_quotes + us_quotes

        if all_quotes:
            # 保存 A股数据到数据库
            if cn_quotes:
                try:
                    await self.quote_repo.save_quotes(cn_quotes)
                    logger.debug(f"Saved {len(cn_quotes)} CN watchlist quotes to database")
                except Exception as e:
                    logger.warning(f"Failed to save watchlist quotes: {e}")

            # 获取走势图数据（最近7天收盘价）
            history_map = {}

            # A股走势
            for code in cn_codes:
                try:
                    history = self.client.get_stock_history(code, period="daily")
                    if history:
                        history_map[code] = [h["close"] for h in history[-7:]]
                except Exception as e:
                    logger.debug(f"Failed to get CN history for {code}: {e}")

            # 港股走势
            for code in hk_codes:
                try:
                    history = self.client.get_hk_stock_history(code, period="daily")
                    if history:
                        history_map[code] = [h["close"] for h in history[-7:]]
                except Exception as e:
                    logger.debug(f"Failed to get HK history for {code}: {e}")

            # 更新缓存（使用统一的数据构建方法）
            quote_map = {q["code"]: q for q in all_quotes}
            result = []
            for item in watchlist:
                quote = quote_map.get(item.code, {})
                history_data = history_map.get(item.code, [])
                result.append(self._build_watchlist_item(item, quote, history_data))

            # 更新缓存，非交易时间延长缓存时间
            cache_ttl = (
                CACHE_TTL_REALTIME if self._is_trading_time() else CACHE_TTL_DAILY
            )

            cache_key = self._cache_key("watchlist", user_id, "all")
            await self._set_to_cache(cache_key, result, cache_ttl)

            # 同时更新各市场的缓存
            cn_result = [r for r in result if r["market"] == "CN"]
            hk_result = [r for r in result if r["market"] == "HK"]
            us_result = [r for r in result if r["market"] == "US"]

            cache_key_cn = self._cache_key("watchlist", user_id, "CN")
            cache_key_hk = self._cache_key("watchlist", user_id, "HK")
            cache_key_us = self._cache_key("watchlist", user_id, "US")

            await self._set_to_cache(cache_key_cn, cn_result, cache_ttl)
            await self._set_to_cache(cache_key_hk, hk_result, cache_ttl)
            await self._set_to_cache(cache_key_us, us_result, cache_ttl)

            logger.info(f"Synced watchlist data for {user_id}: {len(result)} stocks (CN:{len(cn_result)}, HK:{len(hk_result)}, US:{len(us_result)})")

    async def get_all_watchlist_users(self) -> List[str]:
        """获取所有有自选股的用户ID（供后台任务调用）"""
        try:
            return await self.watchlist_repo.get_all_users()
        except Exception as e:
            logger.error(f"Failed to get watchlist users: {e}")
            return ["default"]

    async def add_to_watchlist(
        self, code: str, user_id: str = "default", name: str = None, market: str = "CN"
    ) -> Dict[str, Any]:
        """添加到自选"""
        item = await self.watchlist_repo.add_to_watchlist(
            user_id=user_id, code=code, name=name, market=market
        )

        # 清除所有相关缓存
        await self._clear_watchlist_cache(user_id)

        return {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "market": item.market,
        }

    async def remove_from_watchlist(self, code: str, user_id: str = "default") -> bool:
        """从自选移除"""
        result = await self.watchlist_repo.remove_from_watchlist(user_id, code)

        # 清除所有相关缓存
        await self._clear_watchlist_cache(user_id)

        return result

    async def _clear_watchlist_cache(self, user_id: str = "default"):
        """清除自选股相关的所有缓存"""
        # 清除不同市场的缓存
        await self._delete_from_cache(self._cache_key("watchlist", user_id, "all"))
        await self._delete_from_cache(self._cache_key("watchlist", user_id, "CN"))
        await self._delete_from_cache(self._cache_key("watchlist", user_id, "HK"))
        await self._delete_from_cache(self._cache_key("watchlist", user_id, "US"))

    async def is_in_watchlist(self, code: str, user_id: str = "default") -> bool:
        """检查是否在自选中"""
        return await self.watchlist_repo.is_in_watchlist(user_id, code)
