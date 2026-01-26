"""
基金数据客户端 - 使用 AKShare
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

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

    # ==================== 场外基金排行榜和详情 ====================

    # 场外基金列表缓存
    _otc_fund_cache = None
    _otc_fund_cache_time = 0
    _OTC_FUND_CACHE_TTL = 300  # 缓存 5 分钟

    def _get_otc_fund_list_cached(self) -> List[Dict]:
        """获取缓存的场外基金列表"""
        now = time.time()

        if (
            FundClient._otc_fund_cache is not None
            and now - FundClient._otc_fund_cache_time < self._OTC_FUND_CACHE_TTL
        ):
            return FundClient._otc_fund_cache

        logger.info("Fetching OTC fund list from AKShare...")
        try:
            df = ak.fund_open_fund_rank_em(symbol="全部")
            result = []

            for _, row in df.iterrows():
                fund_name = str(row.get("基金简称", ""))
                fund_type = self._infer_fund_type(fund_name)

                result.append({
                    "code": row["基金代码"],
                    "name": fund_name,
                    "fund_type": fund_type,
                    "nav": float(row.get("单位净值", 0) or 0),
                    "acc_nav": float(row.get("累计净值", 0) or 0),
                    "change_percent": float(row.get("日增长率", 0) or 0),
                    "return_1w": float(row.get("近1周", 0) or 0),
                    "return_1m": float(row.get("近1月", 0) or 0),
                    "return_3m": float(row.get("近3月", 0) or 0),
                    "return_6m": float(row.get("近6月", 0) or 0),
                    "return_1y": float(row.get("近1年", 0) or 0),
                    "return_ytd": float(row.get("今年来", 0) or 0),
                })

            FundClient._otc_fund_cache = result
            FundClient._otc_fund_cache_time = now
            logger.info(f"OTC fund list cached: {len(result)} funds")
            return result
        except Exception as e:
            logger.error(f"Failed to fetch OTC fund list: {e}")
            if FundClient._otc_fund_cache is not None:
                return FundClient._otc_fund_cache
            return []

    def get_fund_ranking(
        self,
        fund_type: str = None,
        sort_by: str = "return_1y",
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取基金排行榜
        :param fund_type: 基金类型（股票型/混合型/债券型/指数型/QDII）
        :param sort_by: 排序字段（return_1w/return_1m/return_3m/return_6m/return_1y/return_ytd）
        :param limit: 返回数量
        """
        funds = self._get_otc_fund_list_cached()

        # 按类型过滤
        if fund_type and fund_type != "全部":
            funds = [f for f in funds if f["fund_type"] == fund_type]

        # 排序（降序）
        valid_sort_fields = ["return_1w", "return_1m", "return_3m", "return_6m", "return_1y", "return_ytd", "change_percent"]
        if sort_by not in valid_sort_fields:
            sort_by = "return_1y"

        funds = sorted(funds, key=lambda x: x.get(sort_by, 0) or 0, reverse=True)

        return funds[:limit]

    def get_fund_detail(self, code: str) -> Optional[Dict[str, Any]]:
        """获取基金详情"""
        try:
            # 基本信息
            df = ak.fund_individual_basic_info_xq(symbol=code)
            info = {row["item"]: row["value"] for _, row in df.iterrows()}

            # 从缓存获取实时数据
            funds = self._get_otc_fund_list_cached()
            realtime = next((f for f in funds if f["code"] == code), {})

            result = {
                "code": code,
                "name": info.get("基金名称", realtime.get("name", "")),
                "full_name": info.get("基金全称", ""),
                "fund_type": info.get("基金类型", realtime.get("fund_type", "")),
                "establish_date": info.get("成立时间", ""),
                "asset_size": info.get("最新规模", ""),
                "company": info.get("基金公司", ""),
                "manager": info.get("基金经理", ""),
                "custodian": info.get("托管银行", ""),
                "benchmark": info.get("业绩比较基准", ""),
                "investment_target": info.get("投资目标", ""),
                "investment_strategy": info.get("投资策略", ""),
                # 实时数据
                "nav": realtime.get("nav", 0),
                "acc_nav": realtime.get("acc_nav", 0),
                "change_percent": realtime.get("change_percent", 0),
                "return_1w": realtime.get("return_1w", 0),
                "return_1m": realtime.get("return_1m", 0),
                "return_3m": realtime.get("return_3m", 0),
                "return_6m": realtime.get("return_6m", 0),
                "return_1y": realtime.get("return_1y", 0),
                "return_ytd": realtime.get("return_ytd", 0),
            }

            return result
        except Exception as e:
            logger.error(f"Failed to get fund detail for {code}: {e}")
            # 退而求其次，返回缓存中的数据
            funds = self._get_otc_fund_list_cached()
            fund = next((f for f in funds if f["code"] == code), None)
            return fund

    def search_otc_fund(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索场外基金（使用缓存）"""
        funds = self._get_otc_fund_list_cached()

        results = []
        keyword_lower = keyword.lower()

        for fund in funds:
            code = fund.get("code", "")
            name = fund.get("name", "")

            if keyword_lower in code.lower() or keyword in name:
                results.append(fund)
                if len(results) >= 20:
                    break

        return results

    # ==================== 场内基金（ETF）相关方法 ====================

    # ETF 列表缓存
    _etf_list_cache = None
    _etf_list_cache_time = 0
    _ETF_LIST_CACHE_TTL = 3600  # 缓存 1 小时

    def _get_etf_list_cached(self) -> List[Dict]:
        """获取缓存的 ETF 列表（使用新浪全量数据）"""
        import time

        now = time.time()

        # 检查缓存是否有效
        if (
            FundClient._etf_list_cache is not None
            and now - FundClient._etf_list_cache_time < self._ETF_LIST_CACHE_TTL
        ):
            logger.debug("Using cached ETF list")
            return FundClient._etf_list_cache

        logger.info("Fetching ETF list from AKShare...")
        try:
            df = ak.fund_etf_category_sina(symbol="ETF基金")
            result = []
            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                # 去掉前缀 (sh/sz)
                if code.startswith("sh") or code.startswith("sz"):
                    code = code[2:]

                result.append({
                    "code": code,
                    "name": row.get("名称", ""),
                    "price": float(row.get("最新价", 0) or 0),
                    "change": float(row.get("涨跌额", 0) or 0),
                    "change_percent": float(row.get("涨跌幅", 0) or 0),
                    "open": float(row.get("今开", 0) or 0),
                    "high": float(row.get("最高", 0) or 0),
                    "low": float(row.get("最低", 0) or 0),
                    "prev_close": float(row.get("昨收", 0) or 0),
                    "volume": int(float(row.get("成交量", 0) or 0)),
                    "amount": float(row.get("成交额", 0) or 0),
                    "etf_type": self._infer_etf_type(row.get("名称", "")),
                })

            FundClient._etf_list_cache = result
            FundClient._etf_list_cache_time = now
            logger.info(f"ETF list cached: {len(result)} ETFs")
            return result
        except Exception as e:
            logger.error(f"Failed to fetch ETF list: {e}")
            if FundClient._etf_list_cache is not None:
                return FundClient._etf_list_cache
            return []

    def _infer_etf_type(self, name: str) -> str:
        """从 ETF 名称推断类型"""
        name_upper = name.upper()

        # 跨境 ETF
        if any(k in name for k in ["纳斯达克", "标普", "日经", "恒生", "德国", "法国", "港股", "美国", "日本"]):
            return "跨境ETF"

        # 商品 ETF
        if any(k in name for k in ["黄金", "白银", "原油", "豆粕", "有色", "能源化工"]):
            return "商品ETF"

        # 债券 ETF
        if any(k in name for k in ["国债", "企债", "信用债", "可转债", "利率"]):
            return "债券ETF"

        # 行业 ETF
        industry_keywords = [
            "银行", "证券", "保险", "金融", "地产", "房地产",
            "医药", "医疗", "生物", "芯片", "半导体", "科技", "通信", "5G",
            "新能源", "光伏", "电池", "汽车", "军工", "国防",
            "消费", "食品", "白酒", "家电", "农业", "畜牧",
            "传媒", "游戏", "互联网", "软件", "计算机",
            "钢铁", "煤炭", "有色", "化工", "建材", "机械",
        ]
        if any(k in name for k in industry_keywords):
            return "行业ETF"

        # 宽基 ETF
        if any(k in name for k in ["沪深300", "中证500", "中证1000", "上证50", "创业板", "科创", "深证", "上证"]):
            return "宽基ETF"

        return "其他ETF"

    def get_etf_realtime(self, codes: List[str] = None) -> List[Dict[str, Any]]:
        """获取 ETF 实时行情"""
        etf_list = self._get_etf_list_cached()

        if codes:
            # 过滤指定代码
            code_set = set(codes)
            return [etf for etf in etf_list if etf["code"] in code_set]

        return etf_list

    def get_etf_history(
        self,
        code: str,
        period: str = "daily",
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """获取 ETF 历史数据"""
        try:
            df = ak.fund_etf_hist_em(symbol=code, period=period, adjust="qfq")

            if df is None or df.empty:
                return []

            # 取最近 N 天
            df = df.tail(days)

            result = []
            for _, row in df.iterrows():
                result.append({
                    "date": str(row["日期"])[-5:] if len(str(row["日期"])) >= 5 else str(row["日期"]),
                    "open": float(row.get("开盘", 0) or 0),
                    "close": float(row.get("收盘", 0) or 0),
                    "high": float(row.get("最高", 0) or 0),
                    "low": float(row.get("最低", 0) or 0),
                    "volume": int(row.get("成交量", 0) or 0),
                    "amount": float(row.get("成交额", 0) or 0),
                    "change_percent": float(row.get("涨跌幅", 0) or 0),
                    "turnover": float(row.get("换手率", 0) or 0),
                })

            return result
        except Exception as e:
            logger.error(f"Failed to get ETF history for {code}: {e}")
            return []

    def search_etf(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索 ETF"""
        etf_list = self._get_etf_list_cached()

        results = []
        keyword_lower = keyword.lower()

        for etf in etf_list:
            code = etf.get("code", "")
            name = etf.get("name", "")

            if keyword_lower in code.lower() or keyword in name:
                results.append(etf)
                if len(results) >= 20:
                    break

        return results

    def get_hot_etfs(self) -> List[Dict[str, Any]]:
        """获取热门 ETF（用于首页展示）"""
        # 热门 ETF 代码列表
        hot_codes = [
            "510300",  # 沪深300ETF
            "510500",  # 中证500ETF
            "159915",  # 创业板ETF
            "588000",  # 科创50ETF
            "512880",  # 证券ETF
            "512010",  # 医药ETF
            "515790",  # 光伏ETF
            "512480",  # 半导体ETF
            "516160",  # 新能源ETF
            "159941",  # 纳指ETF
        ]

        etf_list = self._get_etf_list_cached()
        etf_map = {etf["code"]: etf for etf in etf_list}

        result = []
        for code in hot_codes:
            if code in etf_map:
                result.append(etf_map[code])

        return result
