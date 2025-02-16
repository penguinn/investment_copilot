from typing import Any, Dict

import akshare as ak

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
                return self._get_cn_market_data(symbol, period)
            elif market == "HK":
                return self._get_hk_market_data(symbol, period)
            elif market == "US":
                return self._get_us_market_data(symbol, period)
            else:
                raise ValueError(f"Unsupported market: {market}")
        except Exception as e:
            self.handle_error(e, {"market": market, "symbol": symbol, "period": period})
            raise

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
