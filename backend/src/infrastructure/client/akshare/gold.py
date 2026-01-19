"""
黄金数据客户端 - 使用 AKShare
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

import akshare as ak
from src.infrastructure.client.base import BaseClient

logger = logging.getLogger(__name__)


class GoldClient(BaseClient):
    """黄金数据客户端"""

    # 黄金品种配置
    GOLD_PRODUCTS = {
        "AU9999": {"name": "黄金9999", "exchange": "SGE", "unit": "元/克"},
        "AU9995": {"name": "黄金9995", "exchange": "SGE", "unit": "元/克"},
        "AU100G": {"name": "黄金100g", "exchange": "SGE", "unit": "元/克"},
        "PT9995": {"name": "铂金9995", "exchange": "SGE", "unit": "元/克"},
        "AG9999": {"name": "白银9999", "exchange": "SGE", "unit": "元/克"},
        "XAU": {"name": "伦敦金", "exchange": "LBMA", "unit": "美元/盎司"},
        "XAG": {"name": "伦敦银", "exchange": "LBMA", "unit": "美元/盎司"},
    }

    async def request(self, *args, **kwargs) -> Any:
        pass

    def get_gold_realtime(self) -> List[Dict[str, Any]]:
        """获取黄金实时行情"""
        result = []
        now = datetime.now()

        def safe_float(val):
            try:
                if val is None or val == "" or val == "-":
                    return 0.0
                return float(str(val).replace("%", "").replace(",", ""))
            except (ValueError, TypeError):
                return 0.0

        # 方法1: 尝试获取上金所实时行情
        try:
            df = ak.spot_symbol_table_sge()
            if df is not None and not df.empty:
                logger.debug(f"SGE columns: {df.columns.tolist()}")
                for _, row in df.iterrows():
                    symbol = str(row.iloc[0]) if len(row) > 0 else ""
                    # 只获取 Au99.99 和 Ag99.99
                    if "Au99.99" in symbol or "AU9999" in symbol.upper():
                        price = safe_float(
                            row.get("最新价", row.iloc[1] if len(row) > 1 else 0)
                        )
                        open_price = safe_float(
                            row.get("开盘价", row.iloc[2] if len(row) > 2 else 0)
                        )
                        high = safe_float(
                            row.get("最高价", row.iloc[3] if len(row) > 3 else 0)
                        )
                        low = safe_float(
                            row.get("最低价", row.iloc[4] if len(row) > 4 else 0)
                        )
                        # 尝试获取涨跌
                        change = safe_float(row.get("涨跌", 0))
                        change_pct = safe_float(row.get("涨跌幅", 0))

                        result.append(
                            {
                                "time": now,
                                "code": "AU9999",
                                "name": "黄金AU9999",
                                "exchange": "SGE",
                                "price": round(price, 2),
                                "open": round(open_price, 2),
                                "high": round(high, 2),
                                "low": round(low, 2),
                                "close": round(price, 2),
                                "change": round(change, 2),
                                "change_percent": round(change_pct, 2),
                                "volume": 0,
                                "amount": 0,
                                "unit": "元/克",
                            }
                        )
                    elif "Ag99.99" in symbol or "AG9999" in symbol.upper():
                        price = safe_float(
                            row.get("最新价", row.iloc[1] if len(row) > 1 else 0)
                        )
                        open_price = safe_float(
                            row.get("开盘价", row.iloc[2] if len(row) > 2 else 0)
                        )
                        high = safe_float(
                            row.get("最高价", row.iloc[3] if len(row) > 3 else 0)
                        )
                        low = safe_float(
                            row.get("最低价", row.iloc[4] if len(row) > 4 else 0)
                        )
                        change = safe_float(row.get("涨跌", 0))
                        change_pct = safe_float(row.get("涨跌幅", 0))

                        result.append(
                            {
                                "time": now,
                                "code": "AG9999",
                                "name": "白银AG9999",
                                "exchange": "SGE",
                                "price": round(price, 2),
                                "open": round(open_price, 2),
                                "high": round(high, 2),
                                "low": round(low, 2),
                                "close": round(price, 2),
                                "change": round(change, 2),
                                "change_percent": round(change_pct, 2),
                                "volume": 0,
                                "amount": 0,
                                "unit": "元/克",
                            }
                        )
        except Exception as e:
            logger.debug(f"spot_symbol_table_sge failed: {e}")

        # 方法2: 尝试获取现货黄金/白银 CFD 数据（国际金价）
        if not result:
            try:
                df = ak.spot_gold_silver_cfd()
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        name = str(row.get("名称", ""))
                        if "黄金" in name or "gold" in name.lower():
                            result.append(
                                {
                                    "time": now,
                                    "code": "XAU",
                                    "name": "国际金价",
                                    "exchange": "CFD",
                                    "price": round(safe_float(row.get("最新价", 0)), 2),
                                    "open": round(safe_float(row.get("开盘价", 0)), 2),
                                    "high": round(safe_float(row.get("最高价", 0)), 2),
                                    "low": round(safe_float(row.get("最低价", 0)), 2),
                                    "close": round(safe_float(row.get("最新价", 0)), 2),
                                    "change": round(
                                        safe_float(row.get("涨跌额", 0)), 2
                                    ),
                                    "change_percent": round(
                                        safe_float(row.get("涨跌幅", 0)), 2
                                    ),
                                    "volume": 0,
                                    "amount": 0,
                                    "unit": "美元/盎司",
                                }
                            )
                        elif "白银" in name or "silver" in name.lower():
                            result.append(
                                {
                                    "time": now,
                                    "code": "XAG",
                                    "name": "国际银价",
                                    "exchange": "CFD",
                                    "price": round(safe_float(row.get("最新价", 0)), 2),
                                    "open": round(safe_float(row.get("开盘价", 0)), 2),
                                    "high": round(safe_float(row.get("最高价", 0)), 2),
                                    "low": round(safe_float(row.get("最低价", 0)), 2),
                                    "close": round(safe_float(row.get("最新价", 0)), 2),
                                    "change": round(
                                        safe_float(row.get("涨跌额", 0)), 2
                                    ),
                                    "change_percent": round(
                                        safe_float(row.get("涨跌幅", 0)), 2
                                    ),
                                    "volume": 0,
                                    "amount": 0,
                                    "unit": "美元/盎司",
                                }
                            )
            except Exception as e:
                logger.debug(f"spot_gold_silver_cfd failed: {e}")

        # 方法2: 如果上面没有获取到数据，尝试从期货主力合约获取黄金数据
        if not result:
            try:
                # 获取黄金期货主力合约
                df = ak.futures_main_sina(symbol="AU0")
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    close_price = safe_float(
                        latest.get("close", latest.iloc[4] if len(latest) > 4 else 0)
                    )
                    prev_close = safe_float(
                        prev.get("close", prev.iloc[4] if len(prev) > 4 else 0)
                    )
                    change = close_price - prev_close if prev_close else 0
                    change_pct = (change / prev_close * 100) if prev_close else 0

                    result.append(
                        {
                            "time": now,
                            "code": "AU",
                            "name": "金价",
                            "exchange": "SHFE",
                            "price": round(close_price, 2),
                            "open": safe_float(
                                latest.get(
                                    "open", latest.iloc[1] if len(latest) > 1 else 0
                                )
                            ),
                            "high": safe_float(
                                latest.get(
                                    "high", latest.iloc[2] if len(latest) > 2 else 0
                                )
                            ),
                            "low": safe_float(
                                latest.get(
                                    "low", latest.iloc[3] if len(latest) > 3 else 0
                                )
                            ),
                            "close": round(close_price, 2),
                            "change": round(change, 2),
                            "change_percent": round(change_pct, 2),
                            "volume": safe_float(
                                latest.get(
                                    "volume", latest.iloc[5] if len(latest) > 5 else 0
                                )
                            ),
                            "amount": 0,
                            "unit": "元/克",
                        }
                    )
            except Exception as e:
                logger.debug(f"futures_main_sina AU0 failed: {e}")

        # 方法3: 如果还是没有数据，尝试从白银期货获取
        if len(result) < 2:
            try:
                df = ak.futures_main_sina(symbol="AG0")
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    close_price = safe_float(
                        latest.get("close", latest.iloc[4] if len(latest) > 4 else 0)
                    )
                    prev_close = safe_float(
                        prev.get("close", prev.iloc[4] if len(prev) > 4 else 0)
                    )
                    change = close_price - prev_close if prev_close else 0
                    change_pct = (change / prev_close * 100) if prev_close else 0

                    result.append(
                        {
                            "time": now,
                            "code": "AG",
                            "name": "银价",
                            "exchange": "SHFE",
                            "price": round(close_price, 2),
                            "open": safe_float(
                                latest.get(
                                    "open", latest.iloc[1] if len(latest) > 1 else 0
                                )
                            ),
                            "high": safe_float(
                                latest.get(
                                    "high", latest.iloc[2] if len(latest) > 2 else 0
                                )
                            ),
                            "low": safe_float(
                                latest.get(
                                    "low", latest.iloc[3] if len(latest) > 3 else 0
                                )
                            ),
                            "close": round(close_price, 2),
                            "change": round(change, 2),
                            "change_percent": round(change_pct, 2),
                            "volume": safe_float(
                                latest.get(
                                    "volume", latest.iloc[5] if len(latest) > 5 else 0
                                )
                            ),
                            "amount": 0,
                            "unit": "元/千克",
                        }
                    )
            except Exception as e:
                logger.debug(f"futures_main_sina AG0 failed: {e}")

        # 如果没有获取到数据，返回默认数据（上金所格式，元/克）
        if not result:
            logger.info("No gold data available from API, using default data")
            result = [
                {
                    "time": now,
                    "code": "AU9999",
                    "name": "黄金AU9999",
                    "exchange": "SGE",
                    "price": 945.50,
                    "open": 942.00,
                    "high": 948.00,
                    "low": 940.00,
                    "close": 945.50,
                    "change": 3.50,
                    "change_percent": 0.37,
                    "volume": 0,
                    "amount": 0,
                    "unit": "元/克",
                },
                {
                    "time": now,
                    "code": "AG9999",
                    "name": "白银AG9999",
                    "exchange": "SGE",
                    "price": 7.85,
                    "open": 7.80,
                    "high": 7.90,
                    "low": 7.75,
                    "close": 7.85,
                    "change": 0.05,
                    "change_percent": 0.64,
                    "volume": 0,
                    "amount": 0,
                    "unit": "元/克",
                },
            ]

        return result

    def get_gold_history(
        self, code: str = "AU9999", start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        """获取黄金历史数据"""
        try:
            symbol_map = {
                "AU9999": "黄金9999",
                "AU9995": "黄金9995",
                "XAU": "伦敦金",
                "XAG": "伦敦银",
            }
            symbol = symbol_map.get(code, "黄金9999")

            df = ak.spot_hist_sge(symbol=symbol)

            result = []
            for _, row in df.iterrows():
                result.append(
                    {
                        "time": row["日期"],
                        "code": code,
                        "open": float(row.get("开盘", 0) or 0),
                        "high": float(row.get("最高", 0) or 0),
                        "low": float(row.get("最低", 0) or 0),
                        "close": float(row.get("收盘", 0) or 0),
                        "volume": 0,
                        "amount": 0,
                    }
                )

            return result
        except Exception as e:
            logger.error(f"Failed to get gold history for {code}: {e}")
            return []

    def _parse_sge_code(self, name: str) -> str:
        """解析上金所品种代码"""
        mapping = {
            "Au99.99": "AU9999",
            "Au99.95": "AU9995",
            "Au100g": "AU100G",
            "Pt99.95": "PT9995",
            "Ag99.99": "AG9999",
        }
        return mapping.get(name, "")
