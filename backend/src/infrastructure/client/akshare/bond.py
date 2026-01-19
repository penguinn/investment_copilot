"""
债券数据客户端 - 使用 AKShare
"""
import logging
from datetime import datetime
from typing import Any, Dict, List

import akshare as ak

from src.infrastructure.client.base import BaseClient

logger = logging.getLogger(__name__)


class BondClient(BaseClient):
    """债券数据客户端"""

    async def request(self, *args, **kwargs) -> Any:
        pass

    def get_treasury_yield(self) -> List[Dict[str, Any]]:
        """获取中国国债收益率"""
        try:
            df = ak.bond_china_yield()
            
            result = []
            now = datetime.now()
            
            # 取最新一天的数据
            if not df.empty:
                latest_date = df["日期"].max()
                df = df[df["日期"] == latest_date]
                
                for _, row in df.iterrows():
                    term = row.get("曲线名称", "")
                    if "中债国债" in term:
                        # 解析期限
                        term_str = term.replace("中债国债收益率曲线", "").strip()
                        result.append({
                            "time": now,
                            "country": "CN",
                            "term": term_str,
                            "yield_rate": float(row.get("收益率", 0) or 0),
                            "change": 0,
                            "prev_yield": 0,
                        })
            
            return result
        except Exception as e:
            logger.error(f"Failed to get treasury yield: {e}")
            return []

    def get_bond_realtime(self, bond_type: str = None) -> List[Dict[str, Any]]:
        """
        获取债券实时行情
        :param bond_type: 债券类型 (treasury/corporate/convertible)
        """
        result = []
        now = datetime.now()

        # 获取可转债数据
        if bond_type is None or bond_type == "convertible":
            try:
                df = ak.bond_cb_jsl()
                
                for _, row in df.iterrows():
                    result.append({
                        "time": now,
                        "code": row.get("bond_id", ""),
                        "name": row.get("bond_nm", ""),
                        "bond_type": "convertible",
                        "price": float(row.get("price", 0) or 0),
                        "open": 0,
                        "high": 0,
                        "low": 0,
                        "close": float(row.get("price", 0) or 0),
                        "change": float(row.get("increase_rt", 0) or 0),
                        "change_percent": float(row.get("increase_rt", 0) or 0),
                        "ytm": float(row.get("ytm_rt", 0) or 0),
                        "volume": float(row.get("volume", 0) or 0),
                        "amount": float(row.get("amt", 0) or 0),
                        "convert_premium": float(row.get("premium_rt", 0) or 0),
                        "convert_value": float(row.get("convert_value", 0) or 0),
                    })
            except Exception as e:
                logger.error(f"Failed to get convertible bond data: {e}")

        # 获取国债/企业债数据
        if bond_type is None or bond_type in ["treasury", "corporate"]:
            try:
                df = ak.bond_zh_hs_spot()
                
                for _, row in df.iterrows():
                    bt = self._parse_bond_type(row.get("名称", ""))
                    if bond_type and bt != bond_type:
                        continue
                    
                    result.append({
                        "time": now,
                        "code": row.get("代码", ""),
                        "name": row.get("名称", ""),
                        "bond_type": bt,
                        "price": float(row.get("最新价", 0) or 0),
                        "open": float(row.get("今开", 0) or 0),
                        "high": float(row.get("最高", 0) or 0),
                        "low": float(row.get("最低", 0) or 0),
                        "close": float(row.get("最新价", 0) or 0),
                        "change": float(row.get("涨跌额", 0) or 0),
                        "change_percent": float(row.get("涨跌幅", 0) or 0),
                        "ytm": 0,
                        "volume": float(row.get("成交量", 0) or 0),
                        "amount": float(row.get("成交额", 0) or 0),
                    })
            except Exception as e:
                logger.error(f"Failed to get bond spot data: {e}")

        return result

    def search_bond(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索债券"""
        try:
            # 搜索可转债
            df = ak.bond_cb_jsl()
            
            mask = df["bond_id"].str.contains(keyword, na=False) | \
                   df["bond_nm"].str.contains(keyword, na=False)
            df = df[mask].head(20)
            
            return [
                {
                    "code": row["bond_id"],
                    "name": row["bond_nm"],
                    "bond_type": "convertible",
                    "price": float(row.get("price", 0) or 0),
                    "change_percent": float(row.get("increase_rt", 0) or 0),
                }
                for _, row in df.iterrows()
            ]
        except Exception as e:
            logger.error(f"Failed to search bond: {e}")
            return []

    def _parse_bond_type(self, name: str) -> str:
        """解析债券类型"""
        if "国债" in name:
            return "treasury"
        elif "转债" in name:
            return "convertible"
        else:
            return "corporate"
