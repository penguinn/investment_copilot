"""
外汇数据客户端 - 使用 AKShare
"""
import logging
from datetime import datetime
from typing import Any, Dict, List

import akshare as ak

from src.infrastructure.client.base import BaseClient

logger = logging.getLogger(__name__)


class ForexClient(BaseClient):
    """外汇数据客户端"""

    # 外汇货币对配置
    FOREX_PAIRS = {
        # 人民币汇率
        "USD/CNY": {"name": "美元/人民币", "category": "cny"},
        "EUR/CNY": {"name": "欧元/人民币", "category": "cny"},
        "GBP/CNY": {"name": "英镑/人民币", "category": "cny"},
        "JPY/CNY": {"name": "日元/人民币(100)", "category": "cny"},
        "HKD/CNY": {"name": "港币/人民币", "category": "cny"},
        # 主要货币对
        "EUR/USD": {"name": "欧元/美元", "category": "major"},
        "GBP/USD": {"name": "英镑/美元", "category": "major"},
        "USD/JPY": {"name": "美元/日元", "category": "major"},
        "AUD/USD": {"name": "澳元/美元", "category": "major"},
        "USD/CHF": {"name": "美元/瑞郎", "category": "major"},
        "USD/CAD": {"name": "美元/加元", "category": "major"},
        # 交叉盘
        "EUR/GBP": {"name": "欧元/英镑", "category": "cross"},
        "EUR/JPY": {"name": "欧元/日元", "category": "cross"},
        "GBP/JPY": {"name": "英镑/日元", "category": "cross"},
    }

    async def request(self, *args, **kwargs) -> Any:
        pass

    def get_forex_realtime(self, category: str = None) -> List[Dict[str, Any]]:
        """
        获取外汇实时行情
        :param category: 分类 (cny/major/cross)
        """
        result = []
        now = datetime.now()

        try:
            # 获取外汇实时行情
            df = ak.fx_spot_quote()
            
            for _, row in df.iterrows():
                code = row.get("货币对", "")
                pair_info = self.FOREX_PAIRS.get(code, {})
                
                cat = pair_info.get("category", "other")
                if category and cat != category:
                    continue
                
                price = float(row.get("最新价", 0) or 0)
                prev_close = float(row.get("昨收价", 0) or 0)
                change = price - prev_close if prev_close else 0
                change_percent = (change / prev_close * 100) if prev_close else 0
                
                result.append({
                    "time": now,
                    "code": code,
                    "name": pair_info.get("name", code),
                    "category": cat,
                    "price": price,
                    "open": float(row.get("今开价", 0) or 0),
                    "high": float(row.get("最高价", 0) or 0),
                    "low": float(row.get("最低价", 0) or 0),
                    "close": price,
                    "change": change,
                    "change_percent": change_percent,
                    "bid": float(row.get("买入价", 0) or 0),
                    "ask": float(row.get("卖出价", 0) or 0),
                    "spread": 0,
                })
        except Exception as e:
            logger.error(f"Failed to get forex realtime: {e}")

        # 如果没有数据，获取中国银行外汇牌价
        if not result or category == "cny":
            result.extend(self._get_boc_forex())

        return result

    def _get_boc_forex(self) -> List[Dict[str, Any]]:
        """获取中国银行外汇牌价"""
        result = []
        now = datetime.now()
        
        try:
            df = ak.fx_pair_quote()
            
            for _, row in df.iterrows():
                code = row.get("货币对", "")
                if code not in self.FOREX_PAIRS:
                    continue
                
                pair_info = self.FOREX_PAIRS[code]
                price = float(row.get("最新价", 0) or 0)
                
                result.append({
                    "time": now,
                    "code": code,
                    "name": pair_info["name"],
                    "category": pair_info["category"],
                    "price": price,
                    "open": 0,
                    "high": 0,
                    "low": 0,
                    "close": price,
                    "change": 0,
                    "change_percent": 0,
                    "bid": float(row.get("买入价", 0) or 0),
                    "ask": float(row.get("卖出价", 0) or 0),
                    "spread": 0,
                })
        except Exception as e:
            logger.error(f"Failed to get BOC forex: {e}")
        
        return result

    def get_forex_history(
        self,
        code: str = "USD/CNY",
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """获取外汇历史数据"""
        try:
            # 转换货币对格式
            symbol = code.replace("/", "")
            
            df = ak.fx_hist_em(symbol=symbol)
            
            result = []
            for _, row in df.iterrows():
                result.append({
                    "time": row["日期"],
                    "code": code,
                    "open": float(row.get("开盘", 0) or 0),
                    "high": float(row.get("最高", 0) or 0),
                    "low": float(row.get("最低", 0) or 0),
                    "close": float(row.get("收盘", 0) or 0),
                })
            
            return result
        except Exception as e:
            logger.error(f"Failed to get forex history for {code}: {e}")
            return []
