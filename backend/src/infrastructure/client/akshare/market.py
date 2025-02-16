from datetime import datetime
from typing import Any, Dict

import akshare as ak
import pytz

from ..base import BaseClient


class MarketClient(BaseClient):
    """市场数据客户端"""

    async def request(self, *args, **kwargs) -> Dict[str, Any]:
        """实现基类的request方法"""
        return self.get_market_index(*args, **kwargs)

    def get_market_index(self, market: str, symbol: str, period: str) -> Dict:
        """获取市场指数数据"""
        try:
            if market == "CN":
                data = self._get_cn_market_data(symbol, period)
            elif market == "HK":
                data = self._get_hk_market_data(symbol, period)
            elif market == "US":
                data = self._get_us_market_data(symbol, period)
            else:
                raise ValueError(f"Unsupported market: {market}")

            # 确保数据不为空
            if not data:
                raise ValueError(f"No data returned for {market}:{symbol}")

            # 获取最新数据
            latest_data = data[-1]

            # 打印数据结构以便调试
            print(f"Market data columns for {market}:{symbol}:", latest_data.keys())

            # 获取当前时间（带时区信息）并转换为字符串
            current_time = datetime.now(pytz.timezone("Asia/Shanghai")).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # 转换为统一格式
            return {
                "symbol": symbol,
                "market": market,
                "name": self._get_index_name(market, symbol),
                "time": current_time,
                "open": float(latest_data.get("开盘", 0)),
                "high": float(latest_data.get("最高", 0)),
                "low": float(latest_data.get("最低", 0)),
                "close": float(latest_data.get("收盘", 0)),
                "volume": float(latest_data.get("成交量", 0)),
                "change": float(latest_data.get("涨跌额", 0)),
                "change_percent": float(latest_data.get("涨跌幅", 0)),
            }

        except Exception as e:
            self.handle_error(e, {"market": market, "symbol": symbol, "period": period})
            raise

    def _get_index_name(self, market: str, symbol: str) -> str:
        """获取指数名称"""
        market_indices = {
            "CN": {
                "sh000001": "上证指数",
                "sz399001": "深证成指",
                "sz399006": "创业板指",
            },
            "HK": {
                "hkHSI": "恒生指数",
                "hkHSCEI": "恒生国企指数",
                "hkHSTECH": "恒生科技指数",
            },
            "US": {
                "DJI": "道琼斯工业指数",
                "IXIC": "纳斯达克综合指数",
                "SPX": "标普500指数",
            },
        }
        return market_indices.get(market, {}).get(symbol, symbol)

    def _get_cn_market_data(self, symbol: str, period: str) -> Dict:
        """获取A股市场数据"""
        if period in ["1min", "5min", "15min", "30min", "60min"]:
            minutes = period.replace("min", "")
            df = ak.index_zh_a_hist_min_em(
                symbol=symbol.replace("sh", "").replace("sz", ""), period=minutes
            )
        elif period == "day":
            df = ak.stock_zh_index_daily(symbol=symbol)
        elif period == "week":
            df = ak.stock_zh_index_weekly(symbol=symbol)
        elif period == "month":
            df = ak.stock_zh_index_monthly(symbol=symbol)
        else:
            raise ValueError(f"Unsupported period: {period}")
        return df.to_dict("records")

    def _get_hk_market_data(self, symbol: str, period: str) -> Dict:
        """获取港股市场数据"""
        if period in ["1min", "5min", "15min", "30min", "60min"]:
            minutes = period.replace("min", "")
            df = ak.stock_hk_index_hist_min_em(symbol=symbol, period=minutes)
        else:
            df = ak.stock_hk_index_daily_em(symbol=symbol)
        return df.to_dict("records")

    def _get_us_market_data(self, symbol: str, period: str) -> Dict:
        """获取美股市场数据"""
        if period in ["1min", "5min", "15min", "30min", "60min"]:
            minutes = period.replace("min", "")
            df = ak.stock_us_index_hist_min_em(symbol=symbol, period=minutes)
        else:
            df = ak.stock_us_index_daily_em(symbol=symbol)
        return df.to_dict("records")
