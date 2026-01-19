"""
基金数据客户端 - 使用 AKShare
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

import akshare as ak
from src.infrastructure.client.base import BaseClient

logger = logging.getLogger(__name__)


class FundClient(BaseClient):
    """基金数据客户端"""

    async def request(self, *args, **kwargs) -> Any:
        pass

    def get_fund_list(self, fund_type: str = None) -> List[Dict[str, Any]]:
        """
        获取基金列表
        :param fund_type: 基金类型 (股票型/混合型/债券型/指数型/货币型/QDII)
        """
        try:
            # 获取开放式基金实时数据
            df = ak.fund_open_fund_rank_em(symbol="全部")

            result = []
            for _, row in df.iterrows():
                ft = self._parse_fund_type(row.get("基金类型", ""))
                if fund_type and ft != fund_type:
                    continue

                result.append(
                    {
                        "code": row["基金代码"],
                        "name": row["基金简称"],
                        "fund_type": ft,
                    }
                )

            return result
        except Exception as e:
            logger.error(f"Failed to get fund list: {e}")
            return []

    def get_fund_realtime(self, codes: List[str] = None) -> List[Dict[str, Any]]:
        """获取基金实时净值"""
        try:
            df = ak.fund_open_fund_rank_em(symbol="全部")

            if codes:
                df = df[df["基金代码"].isin(codes)]

            result = []
            now = datetime.now()

            for _, row in df.iterrows():
                try:
                    result.append(
                        {
                            "time": now,
                            "code": row["基金代码"],
                            "name": row["基金简称"],
                            "fund_type": self._parse_fund_type(row.get("基金类型", "")),
                            "nav": float(row.get("单位净值", 0) or 0),
                            "acc_nav": float(row.get("累计净值", 0) or 0),
                            "change_percent": float(row.get("日增长率", 0) or 0),
                            "return_1w": float(row.get("近1周", 0) or 0),
                            "return_1m": float(row.get("近1月", 0) or 0),
                            "return_3m": float(row.get("近3月", 0) or 0),
                            "return_6m": float(row.get("近6月", 0) or 0),
                            "return_1y": float(row.get("近1年", 0) or 0),
                            "return_ytd": float(row.get("今年来", 0) or 0),
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse fund {row.get('基金代码')}: {e}")
                    continue

            return result
        except Exception as e:
            logger.error(f"Failed to get fund realtime: {e}")
            return []

    def get_fund_history(self, code: str) -> List[Dict[str, Any]]:
        """获取基金历史净值"""
        try:
            df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")

            result = []
            for _, row in df.iterrows():
                result.append(
                    {
                        "time": row["净值日期"],
                        "code": code,
                        "nav": float(row["单位净值"]),
                        "acc_nav": float(row.get("累计净值", row["单位净值"])),
                        "change_percent": float(row.get("日增长率", 0) or 0),
                    }
                )

            return result
        except Exception as e:
            logger.error(f"Failed to get fund history for {code}: {e}")
            return []

    def search_fund(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索基金"""
        try:
            df = ak.fund_open_fund_rank_em(symbol="全部")

            # 按代码或名称搜索
            mask = df["基金代码"].str.contains(keyword, na=False) | df[
                "基金简称"
            ].str.contains(keyword, na=False)
            df = df[mask].head(20)

            return [
                {
                    "code": row["基金代码"],
                    "name": row["基金简称"],
                    "fund_type": self._parse_fund_type(row.get("基金类型", "")),
                    "nav": float(row.get("单位净值", 0) or 0),
                    "change_percent": float(row.get("日增长率", 0) or 0),
                }
                for _, row in df.iterrows()
            ]
        except Exception as e:
            logger.error(f"Failed to search fund: {e}")
            return []

    def get_fund_type_summary(self) -> List[Dict[str, Any]]:
        """获取各类型基金的汇总统计数据"""
        import math

        def safe_float(val):
            """安全转换为浮点数，处理 NaN 和空值"""
            try:
                if val is None or val == "" or val == "-":
                    return 0.0
                f = float(val)
                if math.isnan(f) or math.isinf(f):
                    return 0.0
                return f
            except (ValueError, TypeError):
                return 0.0

        try:
            df = ak.fund_open_fund_rank_em(symbol="全部")
            now = datetime.now()

            # 按类型分组统计
            type_stats = {}
            for _, row in df.iterrows():
                # 从基金名称推断类型（因为 API 返回数据中没有基金类型列）
                fund_name = str(row.get("基金简称", ""))
                fund_type = self._infer_fund_type(fund_name)
                if fund_type == "其他":
                    continue

                change_pct = safe_float(row.get("日增长率", 0))

                if fund_type not in type_stats:
                    type_stats[fund_type] = {
                        "total": 0,
                        "rise": 0,
                        "fall": 0,
                        "flat": 0,
                        "change_sum": 0,
                    }

                type_stats[fund_type]["total"] += 1
                type_stats[fund_type]["change_sum"] += change_pct

                if change_pct > 0:
                    type_stats[fund_type]["rise"] += 1
                elif change_pct < 0:
                    type_stats[fund_type]["fall"] += 1
                else:
                    type_stats[fund_type]["flat"] += 1

            # 计算平均值并格式化结果
            result = []
            type_order = ["股票型", "混合型", "债券型", "指数型", "QDII"]

            for fund_type in type_order:
                if fund_type in type_stats:
                    stats = type_stats[fund_type]
                    avg_change = (
                        round(stats["change_sum"] / stats["total"], 2)
                        if stats["total"] > 0
                        else 0
                    )
                    result.append(
                        {
                            "time": now,
                            "code": f"FUND_{fund_type.upper()}",
                            "name": f"{fund_type}",
                            "fund_type": fund_type,
                            "avg_change": avg_change,
                            "total": stats["total"],
                            "rise": stats["rise"],
                            "fall": stats["fall"],
                            "flat": stats["flat"],
                        }
                    )

            return result
        except Exception as e:
            logger.error(f"Failed to get fund type summary: {e}")
            return []

    def _parse_fund_type(self, type_str: str) -> str:
        """解析基金类型"""
        type_mapping = {
            "股票型": "股票型",
            "混合型": "混合型",
            "债券型": "债券型",
            "指数型": "指数型",
            "货币型": "货币型",
            "QDII": "QDII",
            "FOF": "FOF",
        }
        for key, value in type_mapping.items():
            if key in type_str:
                return value
        return "其他"

    def _infer_fund_type(self, fund_name: str) -> str:
        """从基金名称推断基金类型"""
        name = fund_name.upper()

        # 指数型（优先判断，因为 ETF/LOF 可能包含其他关键词）
        if "ETF" in name or "LOF" in name or "指数" in fund_name:
            return "指数型"

        # QDII
        if (
            "QDII" in name
            or "美元" in fund_name
            or "美国" in fund_name
            or "纳斯达克" in fund_name
            or "标普" in fund_name
        ):
            return "QDII"

        # 债券型
        if "债" in fund_name or "利率" in fund_name or "信用" in fund_name:
            return "债券型"

        # 混合型
        if (
            "混合" in fund_name
            or "配置" in fund_name
            or "平衡" in fund_name
            or "灵活" in fund_name
        ):
            return "混合型"

        # 股票型
        if (
            "股票" in fund_name
            or "成长" in fund_name
            or "价值" in fund_name
            or "蓝筹" in fund_name
        ):
            return "股票型"

        # 默认归类为混合型（大部分基金是混合型）
        return "混合型"
