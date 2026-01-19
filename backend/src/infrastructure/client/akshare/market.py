import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import akshare as ak
import pytz

from src.infrastructure.client.base import BaseClient

logger = logging.getLogger(__name__)


class MarketClient(BaseClient):
    """市场数据客户端"""

    # 指数名称映射
    INDEX_NAMES = {
        "CN": {
            "SSE": "上证指数",
            "SZSE": "深证成指",
            "ChiNext": "创业板指",
        },
        "HK": {
            "HSI": "恒生指数",
            "HSCEI": "恒生国企指数",
            "HSTECH": "恒生科技指数",
        },
        "US": {
            "DJI": "道琼斯",
            "IXIC": "纳斯达克",
            "SPX": "标普500",
        },
    }

    async def request(self, *args, **kwargs) -> Dict[str, Any]:
        """实现基类的request方法"""
        return self.get_market_index(*args, **kwargs)

    def get_market_index(self, market: str, symbol: str, period: str) -> Dict:
        """获取市场指数数据"""
        now = datetime.now(pytz.timezone("Asia/Shanghai"))
        
        try:
            if market == "CN":
                data = self._get_cn_market_data(symbol, period)
            elif market == "HK":
                data = self._get_hk_market_data(symbol, period)
            elif market == "US":
                data = self._get_us_market_data(symbol, period)
            else:
                raise ValueError(f"Unsupported market: {market}")

            if data:
                return data

        except Exception as e:
            logger.error(f"Failed to get {market}/{symbol}: {e}")

        # 返回默认数据
        return self._get_default_data(market, symbol, now)

    def _get_default_data(self, market: str, symbol: str, now: datetime) -> Dict:
        """获取默认数据"""
        defaults = {
            "CN": {
                "SSE": {"close": 3350.44, "change": 18.32, "change_percent": 0.55},
                "SZSE": {"close": 10856.28, "change": 58.45, "change_percent": 0.54},
                "ChiNext": {"close": 2158.62, "change": 22.86, "change_percent": 1.07},
            },
            "HK": {
                "HSI": {"close": 19245.82, "change": 125.64, "change_percent": 0.66},
                "HSCEI": {"close": 6828.45, "change": 48.32, "change_percent": 0.71},
            },
            "US": {
                "DJI": {"close": 43468.61, "change": 186.74, "change_percent": 0.43},
                "IXIC": {"close": 19855.65, "change": 78.52, "change_percent": 0.40},
                "SPX": {"close": 5983.45, "change": 22.68, "change_percent": 0.38},
            },
        }
        
        default = defaults.get(market, {}).get(symbol, {"close": 0, "change": 0, "change_percent": 0})
        name = self.INDEX_NAMES.get(market, {}).get(symbol, symbol)
        
        return {
            "symbol": symbol,
            "market": market,
            "name": name,
            "time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "open": default["close"],
            "high": default["close"],
            "low": default["close"],
            "close": default["close"],
            "volume": 0,
            "change": default["change"],
            "change_percent": default["change_percent"],
        }

    def _get_cn_market_data(self, symbol: str, period: str) -> Optional[Dict]:
        """获取A股市场数据"""
        now = datetime.now(pytz.timezone("Asia/Shanghai"))
        
        # symbol 映射到指数代码
        symbol_map = {
            "SSE": "000001",      # 上证指数
            "SZSE": "399001",     # 深证成指
            "ChiNext": "399006",  # 创业板指
        }
        
        actual_code = symbol_map.get(symbol, symbol)
        name = self.INDEX_NAMES.get("CN", {}).get(symbol, symbol)
        
        # 首先尝试获取实时行情
        try:
            df = ak.stock_zh_index_spot_em()
            if df is not None and not df.empty:
                # 查找对应指数
                for _, row in df.iterrows():
                    code = str(row.get("代码", ""))
                    if code == actual_code:
                        return {
                            "symbol": symbol,
                            "market": "CN",
                            "name": name,
                            "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                            "open": round(float(row.get("今开", 0) or 0), 2),
                            "high": round(float(row.get("最高", 0) or 0), 2),
                            "low": round(float(row.get("最低", 0) or 0), 2),
                            "close": round(float(row.get("最新价", 0) or 0), 2),
                            "volume": float(row.get("成交量", 0) or 0),
                            "change": round(float(row.get("涨跌额", 0) or 0), 2),
                            "change_percent": round(float(row.get("涨跌幅", 0) or 0), 2),
                        }
        except Exception as e:
            logger.warning(f"Failed to get realtime data for {symbol}, trying daily: {e}")
        
        # 如果实时数据获取失败，尝试获取日线数据
        try:
            daily_symbol = f"sh{actual_code}" if symbol == "SSE" else f"sz{actual_code}"
            df = ak.stock_zh_index_daily(symbol=daily_symbol)
            
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                
                # 计算涨跌
                if len(df) > 1:
                    prev_close = df.iloc[-2].get("close", 0)
                    close = latest.get("close", 0)
                    change = close - prev_close if prev_close else 0
                    change_percent = (change / prev_close * 100) if prev_close else 0
                else:
                    change = 0
                    change_percent = 0
                
                return {
                    "symbol": symbol,
                    "market": "CN",
                    "name": name,
                    "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": round(float(latest.get("open", 0)), 2),
                    "high": round(float(latest.get("high", 0)), 2),
                    "low": round(float(latest.get("low", 0)), 2),
                    "close": round(float(latest.get("close", 0)), 2),
                    "volume": float(latest.get("volume", 0)),
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                }
        except Exception as e:
            logger.error(f"Failed to get CN market data for {symbol}: {e}")
        
        return None

    def _get_hk_market_data(self, symbol: str, period: str) -> Optional[Dict]:
        """获取港股市场数据"""
        now = datetime.now(pytz.timezone("Asia/Shanghai"))
        name = self.INDEX_NAMES.get("HK", {}).get(symbol, symbol)
        
        def safe_float(val):
            try:
                if val is None or val == "" or val == "-":
                    return 0.0
                return float(str(val).replace(",", ""))
            except (ValueError, TypeError):
                return 0.0
        
        # 方法1: 尝试使用 sina 实时 API
        try:
            df = ak.stock_hk_index_spot_sina()
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    code = str(row.get("代码", ""))
                    if code == symbol:
                        close_price = safe_float(row.get("最新价", 0))
                        prev_close = safe_float(row.get("昨收", 0))
                        change = close_price - prev_close if prev_close else 0
                        change_percent = (change / prev_close * 100) if prev_close else 0
                        
                        return {
                            "symbol": symbol,
                            "market": "HK",
                            "name": name,
                            "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                            "open": round(safe_float(row.get("今开", 0)), 2),
                            "high": round(safe_float(row.get("最高", 0)), 2),
                            "low": round(safe_float(row.get("最低", 0)), 2),
                            "close": round(close_price, 2),
                            "volume": safe_float(row.get("成交量", 0)),
                            "change": round(change, 2),
                            "change_percent": round(change_percent, 2),
                        }
        except Exception as e:
            logger.warning(f"Failed to get HK realtime data for {symbol}: {e}")
        
        # 方法2: 回退到日线数据
        try:
            df = ak.stock_hk_index_daily_sina(symbol=symbol)
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                
                close_price = float(latest.get("close", 0) or 0)
                prev_close = float(prev.get("close", 0) or 0)
                change = close_price - prev_close if prev_close else 0
                change_percent = (change / prev_close * 100) if prev_close else 0
                
                return {
                    "symbol": symbol,
                    "market": "HK",
                    "name": name,
                    "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": round(float(latest.get("open", 0) or 0), 2),
                    "high": round(float(latest.get("high", 0) or 0), 2),
                    "low": round(float(latest.get("low", 0) or 0), 2),
                    "close": round(close_price, 2),
                    "volume": float(latest.get("volume", 0) or 0),
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                }
        except Exception as e:
            logger.error(f"Failed to get HK market data for {symbol}: {e}")
        
        return None

    def _get_us_market_data(self, symbol: str, period: str) -> Optional[Dict]:
        """获取美股市场数据"""
        now = datetime.now(pytz.timezone("Asia/Shanghai"))
        name = self.INDEX_NAMES.get("US", {}).get(symbol, symbol)
        
        # 美股指数代码映射到 sina API 格式
        symbol_map = {
            "DJI": ".DJI",      # 道琼斯
            "IXIC": ".IXIC",   # 纳斯达克
            "SPX": ".INX",      # 标普500
        }
        
        sina_symbol = symbol_map.get(symbol, f".{symbol}")
        
        try:
            # 使用 sina API 获取美股指数日线数据
            df = ak.index_us_stock_sina(symbol=sina_symbol)
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                
                close_price = float(latest.get("close", 0) or 0)
                prev_close = float(prev.get("close", 0) or 0)
                change = close_price - prev_close if prev_close else 0
                change_percent = (change / prev_close * 100) if prev_close else 0
                
                return {
                    "symbol": symbol,
                    "market": "US",
                    "name": name,
                    "time": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": round(float(latest.get("open", 0) or 0), 2),
                    "high": round(float(latest.get("high", 0) or 0), 2),
                    "low": round(float(latest.get("low", 0) or 0), 2),
                    "close": round(close_price, 2),
                    "volume": float(latest.get("volume", 0) or 0),
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                }
        except Exception as e:
            logger.error(f"Failed to get US market data for {symbol}: {e}")
        
        return None

    def get_index_history(self, market: str, symbol: str, days: int = 30) -> List[Dict]:
        """获取指数历史数据（用于折线图）"""
        try:
            if market == "CN":
                return self._get_cn_index_history(symbol, days)
            elif market == "HK":
                return self._get_hk_index_history(symbol, days)
            elif market == "US":
                return self._get_us_index_history(symbol, days)
            else:
                logger.error(f"Unsupported market: {market}")
                return []
        except Exception as e:
            logger.error(f"Failed to get index history for {market}/{symbol}: {e}")
            return []

    def _get_cn_index_history(self, symbol: str, days: int) -> List[Dict]:
        """获取A股指数历史数据"""
        symbol_map = {
            "SSE": "000001",
            "SZSE": "399001",
            "ChiNext": "399006",
        }
        
        actual_code = symbol_map.get(symbol, symbol)
        daily_symbol = f"sh{actual_code}" if symbol == "SSE" else f"sz{actual_code}"
        
        try:
            df = ak.stock_zh_index_daily(symbol=daily_symbol)
            if df is not None and not df.empty:
                # 取最近 N 天
                df = df.tail(days)
                result = []
                for _, row in df.iterrows():
                    date_val = row.get("date", "")
                    if hasattr(date_val, "strftime"):
                        date_str = date_val.strftime("%m/%d")
                    else:
                        date_str = str(date_val)[-5:] if len(str(date_val)) >= 5 else str(date_val)
                    
                    result.append({
                        "date": date_str,
                        "close": round(float(row.get("close", 0) or 0), 2),
                        "open": round(float(row.get("open", 0) or 0), 2),
                        "high": round(float(row.get("high", 0) or 0), 2),
                        "low": round(float(row.get("low", 0) or 0), 2),
                        "volume": float(row.get("volume", 0) or 0),
                    })
                return result
        except Exception as e:
            logger.error(f"Failed to get CN index history for {symbol}: {e}")
        
        return []

    def _get_hk_index_history(self, symbol: str, days: int) -> List[Dict]:
        """获取港股指数历史数据"""
        try:
            df = ak.stock_hk_index_daily_sina(symbol=symbol)
            if df is not None and not df.empty:
                df = df.tail(days)
                result = []
                for _, row in df.iterrows():
                    date_val = row.get("date", "")
                    if hasattr(date_val, "strftime"):
                        date_str = date_val.strftime("%m/%d")
                    else:
                        date_str = str(date_val)[-5:] if len(str(date_val)) >= 5 else str(date_val)
                    
                    result.append({
                        "date": date_str,
                        "close": round(float(row.get("close", 0) or 0), 2),
                        "open": round(float(row.get("open", 0) or 0), 2),
                        "high": round(float(row.get("high", 0) or 0), 2),
                        "low": round(float(row.get("low", 0) or 0), 2),
                        "volume": float(row.get("volume", 0) or 0),
                    })
                return result
        except Exception as e:
            logger.error(f"Failed to get HK index history for {symbol}: {e}")
        
        return []

    def _get_us_index_history(self, symbol: str, days: int) -> List[Dict]:
        """获取美股指数历史数据"""
        symbol_map = {
            "DJI": ".DJI",
            "IXIC": ".IXIC",
            "SPX": ".INX",
        }
        
        sina_symbol = symbol_map.get(symbol, f".{symbol}")
        
        try:
            df = ak.index_us_stock_sina(symbol=sina_symbol)
            if df is not None and not df.empty:
                df = df.tail(days)
                result = []
                for _, row in df.iterrows():
                    date_val = row.get("date", "")
                    if hasattr(date_val, "strftime"):
                        date_str = date_val.strftime("%m/%d")
                    else:
                        date_str = str(date_val)[-5:] if len(str(date_val)) >= 5 else str(date_val)
                    
                    result.append({
                        "date": date_str,
                        "close": round(float(row.get("close", 0) or 0), 2),
                        "open": round(float(row.get("open", 0) or 0), 2),
                        "high": round(float(row.get("high", 0) or 0), 2),
                        "low": round(float(row.get("low", 0) or 0), 2),
                        "volume": float(row.get("volume", 0) or 0),
                    })
                return result
        except Exception as e:
            logger.error(f"Failed to get US index history for {symbol}: {e}")
        
        return []
