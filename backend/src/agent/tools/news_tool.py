"""
新闻工具 - 从数据库获取新闻
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, or_, select

from src.agent.tools.base import BaseTool
from src.infrastructure.db.pgsql import News

logger = logging.getLogger(__name__)


class NewsTool(BaseTool):
    """新闻获取工具"""

    name = "get_news"
    description = """从数据库获取财经新闻。可以按来源、分类、关键词、时间范围等条件筛选。
    
来源(source)可选值：
- cls: 财联社快讯
- eastmoney: 东方财富
- pbc: 中国人民银行
- csrc: 证监会
- ndrc: 发改委
- stats: 国家统计局
- miit: 工信部

分类(category)可选值：
- policy: 政策公告
- news: 市场快讯
- data: 数据发布

使用场景：
- 获取最新市场动态
- 查找特定政策或公告
- 分析某个板块/行业相关新闻
"""

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词，用于在标题和内容中搜索",
                },
                "source": {
                    "type": "string",
                    "description": "新闻来源(cls/eastmoney/pbc/csrc/ndrc/stats/miit)",
                    "enum": ["cls", "eastmoney", "pbc", "csrc", "ndrc", "stats", "miit"],
                },
                "category": {
                    "type": "string",
                    "description": "新闻分类(policy/news/data)",
                    "enum": ["policy", "news", "data"],
                },
                "hours": {
                    "type": "integer",
                    "description": "获取最近多少小时的新闻，默认24小时",
                    "default": 24,
                },
                "min_importance": {
                    "type": "integer",
                    "description": "最小重要性(1-5)，只返回重要性>=该值的新闻",
                    "default": 1,
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量限制，默认20条",
                    "default": 20,
                },
            },
            "required": [],
        }

    def run(
        self,
        keyword: str = None,
        source: str = None,
        category: str = None,
        hours: int = 24,
        min_importance: int = 1,
        limit: int = 20,
    ) -> str:
        """执行新闻查询"""
        try:
            news_list = self._query_news(
                keyword=keyword,
                source=source,
                category=category,
                hours=hours,
                min_importance=min_importance,
                limit=limit,
            )

            if not news_list:
                return "没有找到符合条件的新闻。"

            # 格式化输出
            result_lines = [f"找到 {len(news_list)} 条新闻：\n"]
            for i, news in enumerate(news_list, 1):
                result_lines.append(
                    f"{i}. [{news['source_name']}] {news['title']}\n"
                    f"   时间: {news['publish_time']}\n"
                    f"   摘要: {news['summary'] or news['content'][:100]}...\n"
                    f"   重要性: {news['importance']}/5\n"
                )

            return "\n".join(result_lines)

        except Exception as e:
            logger.error(f"NewsTool error: {e}")
            return f"获取新闻失败: {str(e)}"

    def _query_news(
        self,
        keyword: str = None,
        source: str = None,
        category: str = None,
        hours: int = 24,
        min_importance: int = 1,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """查询新闻"""
        from src.infrastructure.db.database import sync_engine
        from sqlalchemy.orm import Session

        with Session(sync_engine) as session:
            # 构建查询条件
            conditions = [News.is_active == True]

            # 时间范围
            since = datetime.now() - timedelta(hours=hours)
            conditions.append(News.publish_time >= since)

            # 来源过滤
            if source:
                conditions.append(News.source == source)

            # 分类过滤
            if category:
                conditions.append(News.category == category)

            # 重要性过滤
            if min_importance > 1:
                conditions.append(News.importance >= min_importance)

            # 关键词搜索
            if keyword:
                conditions.append(
                    or_(
                        News.title.contains(keyword),
                        News.content.contains(keyword),
                        News.related_sectors.contains(keyword),
                    )
                )

            # 执行查询
            query = (
                select(News)
                .where(and_(*conditions))
                .order_by(desc(News.importance), desc(News.publish_time))
                .limit(limit)
            )

            result = session.execute(query)
            news_list = result.scalars().all()

            return [
                {
                    "id": n.id,
                    "source": n.source,
                    "source_name": n.source_name or n.source,
                    "title": n.title,
                    "content": n.content,
                    "summary": n.summary,
                    "category": n.category,
                    "importance": n.importance,
                    "related_sectors": n.related_sectors,
                    "sentiment": n.sentiment,
                    "publish_time": n.publish_time.strftime("%Y-%m-%d %H:%M") if n.publish_time else "",
                }
                for n in news_list
            ]
