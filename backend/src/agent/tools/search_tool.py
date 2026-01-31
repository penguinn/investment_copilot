"""
搜索工具 - 使用 Tavily API 进行网络搜索
"""

import logging
from typing import Any, Dict, Optional

from src.agent.tools.base import BaseTool
from src.config import TAVILY_API_KEY

logger = logging.getLogger(__name__)


class SearchTool(BaseTool):
    """网络搜索工具"""

    name = "web_search"
    description = """搜索互联网获取最新信息。适用于：
- 查找数据库中没有的最新新闻
- 搜索特定公司、行业的最新动态
- 获取实时市场信息和分析
- 验证或补充数据库中的信息

注意：优先使用 get_news 工具获取数据库中的新闻，只有在需要更多信息时才使用此工具。
"""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """延迟初始化 Tavily 客户端"""
        if self._client is None and TAVILY_API_KEY:
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=TAVILY_API_KEY)
            except ImportError:
                logger.warning("tavily-python not installed")
            except Exception as e:
                logger.error(f"Failed to init Tavily client: {e}")
        return self._client

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询词，建议使用中文或英文关键词组合",
                },
                "search_depth": {
                    "type": "string",
                    "description": "搜索深度: basic(快速) 或 advanced(深度)",
                    "enum": ["basic", "advanced"],
                    "default": "basic",
                },
                "max_results": {
                    "type": "integer",
                    "description": "返回结果数量，默认5条",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    def run(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
    ) -> str:
        """执行搜索"""
        if not TAVILY_API_KEY:
            return "搜索工具未配置，请设置 TAVILY_API_KEY 环境变量。"

        if not self.client:
            return "搜索工具初始化失败。"

        try:
            # 添加财经相关上下文
            enhanced_query = f"{query} 财经 投资"

            response = self.client.search(
                query=enhanced_query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=True,
                include_raw_content=False,
            )

            # 格式化结果
            result_lines = []

            # 如果有直接答案
            if response.get("answer"):
                result_lines.append(f"【摘要】{response['answer']}\n")

            # 搜索结果
            results = response.get("results", [])
            if results:
                result_lines.append(f"找到 {len(results)} 条相关信息：\n")
                for i, item in enumerate(results, 1):
                    result_lines.append(
                        f"{i}. {item.get('title', '无标题')}\n"
                        f"   来源: {item.get('url', '')}\n"
                        f"   内容: {item.get('content', '')[:200]}...\n"
                    )
            else:
                result_lines.append("没有找到相关信息。")

            return "\n".join(result_lines)

        except Exception as e:
            logger.error(f"SearchTool error: {e}")
            return f"搜索失败: {str(e)}"

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(TAVILY_API_KEY)
