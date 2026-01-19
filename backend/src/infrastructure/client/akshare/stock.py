"""
股票数据客户端 - 使用 AKShare
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import akshare as ak
import pandas as pd

from src.infrastructure.client.base import BaseClient

logger = logging.getLogger(__name__)


class StockClient(BaseClient):
    """股票数据客户端"""

    async def request(self, *args, **kwargs) -> Any:
        """实现基类方法"""
        pass

    def get_cn_stock_list(self) -> List[Dict[str, Any]]:
        """获取A股股票列表"""
        try:
            df = ak.stock_zh_a_spot_em()
            return [
                {
                    "code": row["代码"],
                    "name": row["名称"],
                    "market": "CN",
                    "exchange": "SH" if row["代码"].startswith("6") else "SZ",
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
                result.append({
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
                })
            
            return result
        except Exception as e:
            logger.error(f"Failed to get CN stock realtime: {e}")
            return []

    def get_stock_history(
        self,
        code: str,
        period: str = "daily",
        start_date: str = None,
        end_date: str = None,
        adjust: str = "qfq"
    ) -> List[Dict[str, Any]]:
        """
        获取股票历史数据
        :param code: 股票代码
        :param period: 周期 (daily/weekly/monthly)
        :param start_date: 开始日期 YYYYMMDD
        :param end_date: 结束日期 YYYYMMDD
        :param adjust: 复权类型 (qfq前复权/hfq后复权/空字符串不复权)
        """
        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            
            result = []
            for _, row in df.iterrows():
                result.append({
                    "time": pd.to_datetime(row["日期"]),
                    "code": code,
                    "market": "CN",
                    "open": float(row["开盘"]),
                    "high": float(row["最高"]),
                    "low": float(row["最低"]),
                    "close": float(row["收盘"]),
                    "volume": int(row["成交量"]),
                    "amount": float(row["成交额"]),
                    "change": float(row.get("涨跌额", 0) or 0),
                    "change_percent": float(row.get("涨跌幅", 0) or 0),
                    "turnover": float(row.get("换手率", 0) or 0),
                })
            
            return result
        except Exception as e:
            logger.error(f"Failed to get stock history for {code}: {e}")
            return []

    def search_stock(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索股票"""
        try:
            # 获取全部A股列表
            df = ak.stock_zh_a_spot_em()
            
            # 按代码或名称搜索
            mask = df["代码"].str.contains(keyword, na=False) | \
                   df["名称"].str.contains(keyword, na=False)
            df = df[mask].head(20)
            
            return [
                {
                    "code": row["代码"],
                    "name": row["名称"],
                    "market": "CN",
                    "price": float(row.get("最新价", 0) or 0),
                    "change_percent": float(row.get("涨跌幅", 0) or 0),
                }
                for _, row in df.iterrows()
            ]
        except Exception as e:
            logger.error(f"Failed to search stock: {e}")
            return []
