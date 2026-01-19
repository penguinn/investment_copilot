"""
股票数据客户端 - 使用 AKShare
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import akshare as ak
import pandas as pd
from src.infrastructure.client.base import BaseClient

logger = logging.getLogger(__name__)


class StockClient(BaseClient):
    """股票数据客户端"""

    # 类级别的股票列表缓存
    _stock_list_cache: Optional[pd.DataFrame] = None
    _stock_list_cache_time: float = 0
    _stock_list_cache_ttl: int = 3600  # 缓存 1 小时

    async def request(self, *args, **kwargs) -> Any:
        """实现基类方法"""
        pass

    def _get_stock_list_cached(self) -> pd.DataFrame:
        """获取缓存的股票列表"""
        now = time.time()

        # 检查缓存是否有效
        if (
            StockClient._stock_list_cache is not None
            and now - StockClient._stock_list_cache_time
            < StockClient._stock_list_cache_ttl
        ):
            logger.debug("Using cached stock list")
            return StockClient._stock_list_cache

        # 获取新数据
        logger.info("Fetching stock list from AKShare...")
        try:
            df = ak.stock_info_a_code_name()
            StockClient._stock_list_cache = df
            StockClient._stock_list_cache_time = now
            logger.info(f"Stock list cached: {len(df)} stocks")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch stock list: {e}")
            # 如果有旧缓存，继续使用
            if StockClient._stock_list_cache is not None:
                logger.warning("Using stale stock list cache")
                return StockClient._stock_list_cache
            return pd.DataFrame()

    def _get_stock_symbol_with_prefix(self, code: str) -> str:
        """获取带交易所前缀的股票代码

        规则：
        - 6 开头: 上海 (sh)
        - 0, 3 开头: 深圳 (sz)
        - 8, 4 开头: 北交所 (bj)
        """
        if code.startswith("6"):
            return f"sh{code}"
        elif code.startswith(("0", "3")):
            return f"sz{code}"
        elif code.startswith(("8", "4")):
            return f"bj{code}"
        else:
            # 默认上海
            return f"sh{code}"

    def get_cn_stock_list(self) -> List[Dict[str, Any]]:
        """获取A股股票列表"""
        try:
            df = self._get_stock_list_cached()
            return [
                {
                    "code": row["code"],
                    "name": row["name"],
                    "market": "CN",
                    "exchange": "SH" if row["code"].startswith("6") else "SZ",
                }
                for _, row in df.iterrows()
            ]
        except Exception as e:
            logger.error(f"Failed to get CN stock list: {e}")
            return []

    def get_cn_stock_realtime(self, codes: List[str] = None) -> List[Dict[str, Any]]:
        """获取A股实时行情"""
        try:
            df = ak.stock_zh_a_spot_em()

            if codes:
                df = df[df["代码"].isin(codes)]

            result = []
            now = datetime.now()

            for _, row in df.iterrows():
                result.append(
                    {
                        "time": now,
                        "code": row["代码"],
                        "market": "CN",
                        "name": row["名称"],
                        "open": float(row.get("今开", 0) or 0),
                        "high": float(row.get("最高", 0) or 0),
                        "low": float(row.get("最低", 0) or 0),
                        "close": float(row.get("最新价", 0) or 0),
                        "volume": int(row.get("成交量", 0) or 0),
                        "amount": float(row.get("成交额", 0) or 0),
                        "change": float(row.get("涨跌额", 0) or 0),
                        "change_percent": float(row.get("涨跌幅", 0) or 0),
                        "turnover": float(row.get("换手率", 0) or 0),
                        "pe_ratio": float(row.get("市盈率-动态", 0) or 0),
                        "pb_ratio": float(row.get("市净率", 0) or 0),
                        "total_value": float(row.get("总市值", 0) or 0),
                        "circulating_value": float(row.get("流通市值", 0) or 0),
                    }
                )

            return result
        except Exception as e:
            logger.error(f"Failed to get CN stock realtime: {e}")
            return []

    def _get_stock_valuation(self, code: str) -> Dict[str, float]:
        """
        获取股票估值数据（市盈率、市净率、总市值）
        使用 stock_zh_valuation_baidu 接口
        """
        valuation = {"pe_ratio": 0, "pb_ratio": 0, "total_value": 0}

        # 获取市净率
        try:
            df = ak.stock_zh_valuation_baidu(
                symbol=code, indicator="市净率", period="近一年"
            )
            if df is not None and not df.empty:
                valuation["pb_ratio"] = float(df.iloc[-1]["value"])
        except Exception as e:
            logger.debug(f"Failed to get PB ratio for {code}: {e}")

        # 获取市盈率（静态）
        try:
            df = ak.stock_zh_valuation_baidu(
                symbol=code, indicator="市盈率(静)", period="近一年"
            )
            if df is not None and not df.empty:
                valuation["pe_ratio"] = float(df.iloc[-1]["value"])
        except Exception as e:
            logger.debug(f"Failed to get PE ratio for {code}: {e}")

        # 获取总市值（单位：亿）
        try:
            df = ak.stock_zh_valuation_baidu(
                symbol=code, indicator="总市值", period="近一年"
            )
            if df is not None and not df.empty:
                # 百度返回的已经是亿为单位，转为元
                valuation["total_value"] = float(df.iloc[-1]["value"]) * 100000000
        except Exception as e:
            logger.debug(f"Failed to get market cap for {code}: {e}")

        return valuation

    def get_single_stock_realtime(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取单个股票的实时数据
        使用 stock_zh_a_daily 获取个股历史数据（包含最新价格）
        """
        now = datetime.now()

        # 获取股票名称
        stock_list = self._get_stock_list_cached()
        name = ""
        if not stock_list.empty:
            match = stock_list[stock_list["code"] == code]
            if not match.empty:
                name = match.iloc[0]["name"]

        # 使用 stock_zh_a_daily 获取历史数据（需要带前缀）
        try:
            symbol = self._get_stock_symbol_with_prefix(code)
            df = ak.stock_zh_a_daily(symbol=symbol, adjust="qfq")

            if df is not None and not df.empty:
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest

                close = float(latest.get("close", 0))
                prev_close = float(prev.get("close", 0))
                change = close - prev_close if prev_close else 0
                change_percent = (change / prev_close * 100) if prev_close else 0

                # 获取估值数据
                valuation = self._get_stock_valuation(code)

                return {
                    "time": now,
                    "code": code,
                    "market": "CN",
                    "name": name,
                    "open": float(latest.get("open", 0)),
                    "high": float(latest.get("high", 0)),
                    "low": float(latest.get("low", 0)),
                    "close": close,
                    "volume": int(latest.get("volume", 0)),
                    "amount": float(latest.get("amount", 0)),
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                    "turnover": float(latest.get("turnover", 0) or 0),
                    "pe_ratio": valuation["pe_ratio"],
                    "pb_ratio": valuation["pb_ratio"],
                    "total_value": valuation["total_value"],
                    "circulating_value": 0,
                }
        except Exception as e:
            logger.error(
                f"Failed to get single stock data for {code} via stock_zh_a_daily: {e}"
            )

        return None

    def get_stocks_realtime_batch(self, codes: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取股票实时数据
        优先从热门列表获取，不在热门列表的单独获取
        """
        if not codes:
            return []

        result = []
        found_codes = set()

        # 首先尝试从热门列表获取
        try:
            df = ak.stock_zh_a_spot_em()
            for _, row in df.iterrows():
                code = row.get("代码", "")
                if code in codes:
                    now = datetime.now()
                    result.append(
                        {
                            "time": now,
                            "code": code,
                            "market": "CN",
                            "name": row["名称"],
                            "open": float(row.get("今开", 0) or 0),
                            "high": float(row.get("最高", 0) or 0),
                            "low": float(row.get("最低", 0) or 0),
                            "close": float(row.get("最新价", 0) or 0),
                            "volume": int(row.get("成交量", 0) or 0),
                            "amount": float(row.get("成交额", 0) or 0),
                            "change": float(row.get("涨跌额", 0) or 0),
                            "change_percent": float(row.get("涨跌幅", 0) or 0),
                            "turnover": float(row.get("换手率", 0) or 0),
                            "pe_ratio": float(row.get("市盈率-动态", 0) or 0),
                            "pb_ratio": float(row.get("市净率", 0) or 0),
                            "total_value": float(row.get("总市值", 0) or 0),
                            "circulating_value": float(row.get("流通市值", 0) or 0),
                        }
                    )
                    found_codes.add(code)
        except Exception as e:
            logger.warning(f"Failed to get batch realtime from spot: {e}")

        # 对于没找到的股票，单独获取
        missing_codes = set(codes) - found_codes
        for code in missing_codes:
            data = self.get_single_stock_realtime(code)
            if data:
                result.append(data)
            else:
                logger.warning(f"Could not get realtime data for {code}")

        return result

    def get_stock_history(
        self,
        code: str,
        period: str = "daily",
        start_date: str = None,
        end_date: str = None,
        adjust: str = "qfq",
    ) -> List[Dict[str, Any]]:
        """
        获取股票历史数据
        :param code: 股票代码
        :param period: 周期 (daily/weekly/monthly) - 目前只支持 daily
        :param start_date: 开始日期 YYYYMMDD (stock_zh_a_daily 不支持，需要手动过滤)
        :param end_date: 结束日期 YYYYMMDD (stock_zh_a_daily 不支持，需要手动过滤)
        :param adjust: 复权类型 (qfq前复权/hfq后复权/空字符串不复权)
        """
        try:
            symbol = self._get_stock_symbol_with_prefix(code)
            df = ak.stock_zh_a_daily(symbol=symbol, adjust=adjust)

            if df is None or df.empty:
                return []

            # 按日期过滤
            if start_date:
                start_dt = pd.to_datetime(start_date)
                df = df[df["date"] >= start_dt]
            if end_date:
                end_dt = pd.to_datetime(end_date)
                df = df[df["date"] <= end_dt]

            result = []
            for _, row in df.iterrows():
                # 计算涨跌额和涨跌幅（stock_zh_a_daily 不直接提供）
                result.append(
                    {
                        "time": pd.to_datetime(row["date"]),
                        "code": code,
                        "market": "CN",
                        "open": float(row.get("open", 0)),
                        "high": float(row.get("high", 0)),
                        "low": float(row.get("low", 0)),
                        "close": float(row.get("close", 0)),
                        "volume": int(row.get("volume", 0)),
                        "amount": float(row.get("amount", 0)),
                        "change": 0,  # 需要计算
                        "change_percent": 0,  # 需要计算
                        "turnover": float(row.get("turnover", 0) or 0),
                    }
                )

            # 计算涨跌额和涨跌幅
            for i in range(1, len(result)):
                prev_close = result[i - 1]["close"]
                if prev_close > 0:
                    result[i]["change"] = round(result[i]["close"] - prev_close, 2)
                    result[i]["change_percent"] = round(
                        (result[i]["close"] - prev_close) / prev_close * 100, 2
                    )

            return result
        except Exception as e:
            logger.error(f"Failed to get stock history for {code}: {e}")
            return []

    def search_stock(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索股票（使用缓存的股票列表）"""
        try:
            # 使用缓存的股票列表
            df = self._get_stock_list_cached()

            if df.empty:
                return []

            # 按代码或名称搜索
            mask = df["code"].str.contains(keyword, na=False) | df["name"].str.contains(
                keyword, na=False
            )
            df = df[mask].head(20)

            if df.empty:
                return []

            # 获取搜索结果的股票代码
            codes = df["code"].tolist()

            # 尝试获取实时价格
            price_map = {}
            try:
                realtime_df = ak.stock_zh_a_spot_em()
                for _, row in realtime_df.iterrows():
                    code = row.get("代码", "")
                    if code in codes:
                        price_map[code] = {
                            "price": float(row.get("最新价", 0) or 0),
                            "change_percent": float(row.get("涨跌幅", 0) or 0),
                        }
            except Exception as e:
                logger.debug(f"Failed to get realtime prices from spot: {e}")

            # 对于没有实时价格的股票，单独获取
            result = []
            for _, row in df.iterrows():
                code = row["code"]
                if code in price_map:
                    price_info = price_map[code]
                else:
                    # 单独获取这只股票的实时数据
                    single_data = self.get_single_stock_realtime(code)
                    if single_data:
                        price_info = {
                            "price": single_data["close"],
                            "change_percent": single_data["change_percent"],
                        }
                    else:
                        price_info = {"price": 0, "change_percent": 0}

                result.append(
                    {
                        "code": code,
                        "name": row["name"],
                        "market": "CN",
                        "price": price_info["price"],
                        "change_percent": price_info["change_percent"],
                    }
                )

            return result
        except Exception as e:
            logger.error(f"Failed to search stock: {e}")
            return []

    # ========== 港股搜索（使用新浪 API + Redis 缓存） ==========

    # Redis 缓存键
    _HK_STOCK_LIST_CACHE_KEY = "stock_list:HK"
    _US_STOCK_LIST_CACHE_KEY = "stock_list:US"
    _STOCK_LIST_CACHE_TTL = 86400  # 缓存 1 天

    def _get_hk_stock_list_cached(self) -> List[Dict]:
        """获取缓存的港股列表（新浪 API，支持分页获取全量，Redis 缓存）"""
        import json

        import requests
        from src.infrastructure.cache.redis_cache import cache

        # 1. 先从 Redis 获取
        try:
            cached = cache.client.get(self._HK_STOCK_LIST_CACHE_KEY)
            if cached:
                logger.debug("Using Redis cached HK stock list")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Failed to get HK stock list from Redis: {e}")

        # 2. 从新浪 API 获取
        logger.info("Fetching HK stock list from Sina API...")
        all_stocks = []

        # 分页获取全部港股
        for page in range(1, 100):  # 最多100页
            try:
                url = (
                    f"http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
                    f"Market_Center.getHKStockData?page={page}&num=100&sort=symbol&asc=1&node=qbgg_hk"
                )
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if not data:
                        break
                    all_stocks.extend(data)
                else:
                    break
            except Exception as e:
                logger.warning(f"Failed to get HK stocks page {page}: {e}")
                break

        # 3. 存入 Redis
        if all_stocks:
            try:
                cache.client.setex(
                    self._HK_STOCK_LIST_CACHE_KEY,
                    self._STOCK_LIST_CACHE_TTL,
                    json.dumps(all_stocks, ensure_ascii=False),
                )
                logger.info(f"HK stock list cached to Redis: {len(all_stocks)} stocks")
            except Exception as e:
                logger.warning(f"Failed to cache HK stock list to Redis: {e}")

        return all_stocks or []

    def search_hk_stock(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索港股"""
        try:
            stock_list = self._get_hk_stock_list_cached()

            if not stock_list:
                return []

            # 按代码或名称搜索
            results = []
            keyword_lower = keyword.lower()
            for stock in stock_list:
                code = stock.get("symbol", "")
                name = stock.get("name", "")
                if keyword_lower in code.lower() or keyword in name:
                    price = float(stock.get("lasttrade", 0) or 0)
                    change_pct = float(stock.get("changepercent", 0) or 0)
                    results.append(
                        {
                            "code": code,
                            "name": name,
                            "market": "HK",
                            "price": price,
                            "change_percent": change_pct,
                        }
                    )
                    if len(results) >= 20:
                        break

            return results
        except Exception as e:
            logger.error(f"Failed to search HK stock: {e}")
            return []

    def get_hk_stock_realtime(self, codes: List[str]) -> List[Dict[str, Any]]:
        """获取港股实时数据"""
        if not codes:
            return []

        results = []
        now = datetime.now()

        # 从缓存的港股列表获取数据
        stock_list = self._get_hk_stock_list_cached()
        stock_map = {s.get("symbol", ""): s for s in stock_list}

        for code in codes:
            stock = stock_map.get(code)
            if stock:
                # 计算涨跌额
                lasttrade = float(stock.get("lasttrade", 0) or 0)
                prevclose = float(stock.get("prevclose", 0) or 0)
                change = float(stock.get("pricechange", 0) or 0)
                if change == 0 and prevclose > 0:
                    change = lasttrade - prevclose

                results.append(
                    {
                        "time": now,
                        "code": code,
                        "market": "HK",
                        "name": stock.get("name", ""),
                        "open": float(stock.get("open", 0) or 0),
                        "high": float(stock.get("high", 0) or 0),
                        "low": float(stock.get("low", 0) or 0),
                        "close": lasttrade,
                        "volume": int(float(stock.get("volume", 0) or 0)),
                        "amount": float(stock.get("amount", 0) or 0),
                        "change": round(change, 4),
                        "change_percent": float(stock.get("changepercent", 0) or 0),
                        "turnover": 0,  # 新浪 API 不提供换手率
                        "pe_ratio": float(stock.get("pe_ratio", 0) or 0),
                        "pb_ratio": 0,  # 新浪 API 不提供市净率
                        "total_value": float(stock.get("market_value", 0) or 0),
                        "circulating_value": 0,
                    }
                )
            else:
                logger.warning(f"HK stock {code} not found in cache")

        return results

    def get_hk_stock_history(
        self,
        code: str,
        period: str = "daily",
        start_date: str = None,
        end_date: str = None,
    ) -> List[Dict[str, Any]]:
        """
        获取港股历史数据
        使用 AKShare 的 stock_hk_hist 接口
        """
        try:
            df = ak.stock_hk_hist(symbol=code, period=period, adjust="qfq")

            if df is None or df.empty:
                return []

            # 按日期过滤
            if start_date:
                start_dt = pd.to_datetime(start_date)
                df = df[df["日期"] >= start_dt]
            if end_date:
                end_dt = pd.to_datetime(end_date)
                df = df[df["日期"] <= end_dt]

            result = []
            for _, row in df.iterrows():
                result.append(
                    {
                        "time": pd.to_datetime(row["日期"]),
                        "code": code,
                        "market": "HK",
                        "open": float(row.get("开盘", 0) or 0),
                        "high": float(row.get("最高", 0) or 0),
                        "low": float(row.get("最低", 0) or 0),
                        "close": float(row.get("收盘", 0) or 0),
                        "volume": int(row.get("成交量", 0) or 0),
                        "amount": float(row.get("成交额", 0) or 0),
                        "change": float(row.get("涨跌额", 0) or 0),
                        "change_percent": float(row.get("涨跌幅", 0) or 0),
                        "turnover": float(row.get("换手率", 0) or 0),
                    }
                )

            return result
        except Exception as e:
            logger.error(f"Failed to get HK stock history for {code}: {e}")
            return []

    def _get_hk_stock_valuation(self, code: str) -> Dict[str, float]:
        """
        获取港股估值数据（市盈率、市净率、总市值）
        使用 stock_hk_valuation_baidu 接口
        """
        valuation = {"pe_ratio": 0, "pb_ratio": 0, "total_value": 0}

        # 获取市盈率(TTM)
        try:
            df = ak.stock_hk_valuation_baidu(
                symbol=code, indicator="市盈率(TTM)", period="近一年"
            )
            if df is not None and not df.empty:
                valuation["pe_ratio"] = float(df.iloc[-1]["value"])
        except Exception as e:
            logger.debug(f"Failed to get HK PE ratio for {code}: {e}")

        # 获取市净率
        try:
            df = ak.stock_hk_valuation_baidu(
                symbol=code, indicator="市净率", period="近一年"
            )
            if df is not None and not df.empty:
                valuation["pb_ratio"] = float(df.iloc[-1]["value"])
        except Exception as e:
            logger.debug(f"Failed to get HK PB ratio for {code}: {e}")

        # 获取总市值（单位：亿）
        try:
            df = ak.stock_hk_valuation_baidu(
                symbol=code, indicator="总市值", period="近一年"
            )
            if df is not None and not df.empty:
                # 百度返回的是亿为单位，转为元
                valuation["total_value"] = float(df.iloc[-1]["value"]) * 100000000
        except Exception as e:
            logger.debug(f"Failed to get HK market cap for {code}: {e}")

        return valuation

    def get_hk_stock_realtime_with_history(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取港股实时数据（带换手率、市盈率、市值等完整信息）
        """
        try:
            history = self.get_hk_stock_history(code)
            if not history:
                return None

            latest = history[-1]

            # 从缓存获取名称
            stock_list = self._get_hk_stock_list_cached()
            stock_map = {s.get("symbol", ""): s for s in stock_list}
            stock = stock_map.get(code, {})

            # 获取估值数据
            valuation = self._get_hk_stock_valuation(code)

            return {
                "time": latest["time"],
                "code": code,
                "market": "HK",
                "name": stock.get("name", ""),
                "open": latest["open"],
                "high": latest["high"],
                "low": latest["low"],
                "close": latest["close"],
                "volume": latest["volume"],
                "amount": latest["amount"],
                "change": latest["change"],
                "change_percent": latest["change_percent"],
                "turnover": latest["turnover"],
                "pe_ratio": valuation["pe_ratio"],
                "pb_ratio": valuation["pb_ratio"],
                "total_value": valuation["total_value"],
                "circulating_value": 0,
            }
        except Exception as e:
            logger.error(f"Failed to get HK stock realtime for {code}: {e}")
            return None

    # ========== 美股搜索（合并 AKShare 分类 + Redis 缓存） ==========

    def _get_us_stock_list_cached(self) -> List[Dict]:
        """获取缓存的美股列表（合并 AKShare 多个分类，Redis 缓存）"""
        import json

        from src.infrastructure.cache.redis_cache import cache

        # 1. 先从 Redis 获取
        try:
            cached = cache.client.get(self._US_STOCK_LIST_CACHE_KEY)
            if cached:
                logger.debug("Using Redis cached US stock list")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Failed to get US stock list from Redis: {e}")

        # 2. 从 AKShare 获取
        logger.info("Fetching US stock list from AKShare...")
        all_stocks = []
        seen_codes = set()

        # 合并所有分类
        categories = [
            "科技类",
            "金融类",
            "医药食品类",
            "媒体类",
            "汽车能源类",
            "制造零售类",
        ]
        for cat in categories:
            try:
                df = ak.stock_us_famous_spot_em(symbol=cat)
                for _, row in df.iterrows():
                    code = row.get("代码", "")
                    if code and code not in seen_codes:
                        seen_codes.add(code)
                        all_stocks.append(
                            {
                                "code": code,
                                "name": row.get("名称", ""),
                                "price": float(row.get("最新价", 0) or 0),
                                "change_percent": float(row.get("涨跌幅", 0) or 0),
                            }
                        )
            except Exception as e:
                logger.debug(f"Failed to get US stocks ({cat}): {e}")

        # 3. 存入 Redis
        if all_stocks:
            try:
                cache.client.setex(
                    self._US_STOCK_LIST_CACHE_KEY,
                    self._STOCK_LIST_CACHE_TTL,
                    json.dumps(all_stocks, ensure_ascii=False),
                )
                logger.info(f"US stock list cached to Redis: {len(all_stocks)} stocks")
            except Exception as e:
                logger.warning(f"Failed to cache US stock list to Redis: {e}")

        return all_stocks or []

    def search_us_stock(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索美股"""
        try:
            stock_list = self._get_us_stock_list_cached()

            if not stock_list:
                return []

            # 按代码或名称搜索
            results = []
            keyword_lower = keyword.lower()
            for stock in stock_list:
                code = stock.get("code", "")
                name = stock.get("name", "")
                # 代码格式: 105.AAPL, 搜索时也匹配去掉前缀的代码
                code_short = code.split(".")[-1] if "." in code else code
                if (
                    keyword_lower in code.lower()
                    or keyword_lower in code_short.lower()
                    or keyword in name
                ):
                    results.append(
                        {
                            "code": code,
                            "name": name,
                            "market": "US",
                            "price": stock.get("price", 0),
                            "change_percent": stock.get("change_percent", 0),
                        }
                    )
                    if len(results) >= 20:
                        break

            return results
        except Exception as e:
            logger.error(f"Failed to search US stock: {e}")
            return []

    def get_us_stock_realtime(self, codes: List[str]) -> List[Dict[str, Any]]:
        """获取美股实时数据"""
        if not codes:
            return []

        results = []
        now = datetime.now()

        # 从缓存的美股列表获取数据
        stock_list = self._get_us_stock_list_cached()
        stock_map = {s.get("code", ""): s for s in stock_list}

        for code in codes:
            stock = stock_map.get(code)
            if stock:
                results.append(
                    {
                        "time": now,
                        "code": code,
                        "market": "US",
                        "name": stock.get("name", ""),
                        "open": 0,
                        "high": 0,
                        "low": 0,
                        "close": float(stock.get("price", 0) or 0),
                        "volume": 0,
                        "amount": 0,
                        "change": 0,
                        "change_percent": float(stock.get("change_percent", 0) or 0),
                        "turnover": 0,
                        "pe_ratio": 0,
                        "pb_ratio": 0,
                        "total_value": 0,
                        "circulating_value": 0,
                    }
                )
            else:
                logger.warning(f"US stock {code} not found in cache")

        return results
