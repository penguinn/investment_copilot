"""
基金工具 - 获取基金列表和数据
"""

import json
import logging
from typing import Any, Dict, List, Optional

from src.agent.tools.base import BaseTool

logger = logging.getLogger(__name__)


class FundTool(BaseTool):
    """基金数据工具"""

    name = "get_fund_list"
    description = "获取基金列表，包括ETF和热门场外基金。可以按类型筛选（如：军工、新能源、科技、医药、消费等）"

    def __init__(self):
        super().__init__()
        from src.infrastructure.client.akshare.fund import FundClient
        self.client = FundClient()

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "fund_type": {
                    "type": "string",
                    "description": "基金类型筛选关键词，如：军工、新能源、科技、医药、消费、半导体、芯片、银行、证券、房地产等。为空则返回热门基金",
                },
                "market": {
                    "type": "string",
                    "enum": ["ETF", "OTC", "all"],
                    "description": "市场类型：ETF（场内交易型基金）、OTC（场外基金）、all（全部）。默认为all",
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量限制，默认10条",
                },
            },
            "required": [],
        }

    def run(
        self,
        fund_type: Optional[str] = None,
        market: str = "all",
        limit: int = 10,
    ) -> str:
        """
        获取基金列表
        """
        try:
            results = []
            
            # 获取 ETF 列表
            if market in ["ETF", "all"]:
                etf_list = self._get_etf_list(fund_type, limit)
                results.extend(etf_list)
            
            # 获取场外基金列表
            if market in ["OTC", "all"]:
                otc_list = self._get_otc_list(fund_type, limit)
                results.extend(otc_list)
            
            if not results:
                return f"未找到与 '{fund_type}' 相关的基金"
            
            # 格式化输出
            output = []
            if fund_type:
                output.append(f"### {fund_type}相关基金\n")
            else:
                output.append("### 热门基金\n")
            
            for item in results[:limit * 2]:  # 返回限制
                market_type = item.get("market", "")
                name = item.get("name", "")
                code = item.get("code", "")
                change = item.get("change_percent", 0)
                
                if market_type == "ETF":
                    output.append(f"- **{name}**（{code}）[ETF] 涨跌幅: {change:.2f}%")
                else:
                    return_1m = item.get("return_1m", 0)
                    output.append(f"- **{name}**（{code}）[场外] 近1月: {return_1m:.2f}%")
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"获取基金列表失败: {e}")
            return f"获取基金列表失败: {str(e)}"

    def _get_etf_list(self, keyword: Optional[str], limit: int) -> List[Dict]:
        """获取 ETF 列表"""
        try:
            if keyword:
                # 搜索 ETF
                etfs = self.client.search_etf(keyword)
            else:
                # 获取热门 ETF
                etfs = self.client.get_hot_etfs()
            
            # 添加市场标识
            for etf in etfs[:limit]:
                etf["market"] = "ETF"
            
            return etfs[:limit]
        except Exception as e:
            logger.warning(f"获取ETF列表失败: {e}")
            return []

    def _get_otc_list(self, keyword: Optional[str], limit: int) -> List[Dict]:
        """获取场外基金列表"""
        try:
            if keyword:
                # 搜索场外基金
                funds = self.client.search_otc_fund(keyword)
            else:
                # 获取排行榜
                funds = self.client.get_fund_ranking(limit=limit)
            
            # 添加市场标识
            for fund in funds[:limit]:
                fund["market"] = "OTC"
            
            return funds[:limit]
        except Exception as e:
            logger.warning(f"获取场外基金列表失败: {e}")
            return []
