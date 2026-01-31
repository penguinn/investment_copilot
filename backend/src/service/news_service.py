"""
新闻服务层
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import CACHE_TTL_DAILY, CACHE_TTL_REALTIME
from src.infrastructure.client.llm import QwenClient
from src.infrastructure.client.news import NewsClient
from src.infrastructure.db.database import get_db_session
from src.infrastructure.db.pgsql import News
from src.service.base import BaseService

logger = logging.getLogger(__name__)


class NewsService(BaseService):
    """新闻服务"""

    def __init__(self):
        super().__init__("news")
        self.client = NewsClient()
        self.llm_client = QwenClient()

    async def get_latest_news(
        self,
        source: str = None,
        category: str = None,
        limit: int = 50,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        获取最新新闻
        :param source: 来源过滤 (cls/eastmoney/pbc/csrc/ndrc/stats/miit)
        :param category: 分类过滤 (policy/news/data)
        :param limit: 返回数量
        """
        cache_key = self._cache_key(
            "latest", source or "all", category or "all", str(limit)
        )

        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        async with get_db_session() as session:
            query = select(News).where(News.is_active == True)

            if source:
                query = query.where(News.source == source)

            if category:
                query = query.where(News.category == category)

            query = query.order_by(desc(News.publish_time)).limit(limit)

            result = await session.execute(query)
            news_list = result.scalars().all()

            data = [self._news_to_dict(n) for n in news_list]

        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_REALTIME)

        return data

    async def get_important_news(
        self,
        min_importance: int = 3,
        hours: int = 24,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """获取重要新闻"""
        cache_key = self._cache_key(
            "important", str(min_importance), str(hours), str(limit)
        )

        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        since = datetime.now() - timedelta(hours=hours)

        async with get_db_session() as session:
            query = (
                select(News)
                .where(
                    and_(
                        News.is_active == True,
                        News.importance >= min_importance,
                        News.publish_time >= since,
                    )
                )
                .order_by(desc(News.importance), desc(News.publish_time))
                .limit(limit)
            )

            result = await session.execute(query)
            news_list = result.scalars().all()

            data = [self._news_to_dict(n) for n in news_list]

        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_REALTIME)

        return data

    async def get_policy_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取政策新闻"""
        return await self.get_latest_news(category="policy", limit=limit)

    async def get_market_news(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取市场快讯（财联社、东财）"""
        cache_key = self._cache_key("market_news", str(limit))

        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        async with get_db_session() as session:
            query = (
                select(News)
                .where(
                    and_(
                        News.is_active == True,
                        News.source.in_(["cls", "eastmoney"]),
                    )
                )
                .order_by(desc(News.publish_time))
                .limit(limit)
            )

            result = await session.execute(query)
            news_list = result.scalars().all()

            data = [self._news_to_dict(n) for n in news_list]

        if data:
            await self._set_to_cache(cache_key, data, CACHE_TTL_REALTIME)

        return data

    async def search_news(
        self,
        keyword: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """搜索新闻"""
        async with get_db_session() as session:
            query = (
                select(News)
                .where(
                    and_(
                        News.is_active == True,
                        or_(
                            News.title.contains(keyword),
                            News.content.contains(keyword),
                        ),
                    )
                )
                .order_by(desc(News.publish_time))
                .limit(limit)
            )

            result = await session.execute(query)
            news_list = result.scalars().all()

            return [self._news_to_dict(n) for n in news_list]

    async def get_news_by_sector(
        self,
        sector: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """获取某个板块相关的新闻"""
        async with get_db_session() as session:
            query = (
                select(News)
                .where(
                    and_(
                        News.is_active == True,
                        News.related_sectors.contains(sector),
                    )
                )
                .order_by(desc(News.publish_time))
                .limit(limit)
            )

            result = await session.execute(query)
            news_list = result.scalars().all()

            return [self._news_to_dict(n) for n in news_list]

    async def sync_news(self, source: str = None) -> int:
        """
        同步新闻数据
        :param source: 指定来源，None 则同步所有
        :return: 新增新闻数量
        """
        news_list = []

        try:
            if source == "cls" or source is None:
                news_list.extend(self.client.get_cls_telegraph(50))

            if source == "eastmoney" or source is None:
                news_list.extend(self.client.get_eastmoney_news(30))

            if source == "pbc" or source is None:
                news_list.extend(self.client.get_pbc_news(20))

            if source == "csrc" or source is None:
                news_list.extend(self.client.get_csrc_news(20))

            if source == "ndrc" or source is None:
                news_list.extend(self.client.get_ndrc_news(20))

            if source == "stats" or source is None:
                news_list.extend(self.client.get_stats_news(20))

            if source == "miit" or source is None:
                news_list.extend(self.client.get_miit_news(20))

        except Exception as e:
            logger.error(f"Failed to fetch news: {e}")

        if not news_list:
            logger.warning("No news fetched from any source")
            return 0

        logger.info(f"Fetched {len(news_list)} news items, saving to database...")

        # 保存到数据库
        added = 0
        skipped = 0
        errors = 0
        async with get_db_session() as session:
            for news_data in news_list:
                try:
                    # 检查是否已存在（基于来源+标题+发布时间）
                    existing = await session.execute(
                        select(News).where(
                            and_(
                                News.source == news_data["source"],
                                News.title == news_data["title"],
                                News.publish_time == news_data["publish_time"],
                            )
                        )
                    )

                    if existing.scalar_one_or_none():
                        skipped += 1
                        continue

                    # 创建新记录
                    news = News(
                        source=news_data["source"],
                        source_name=news_data.get("source_name", ""),
                        title=news_data.get("title", ""),
                        content=news_data.get("content", ""),
                        url=news_data.get("url", ""),
                        category=news_data.get("category", "news"),
                        publish_time=news_data["publish_time"],
                        importance=news_data.get("importance", 1),
                        related_sectors=news_data.get("related_sectors", ""),
                        crawl_time=datetime.now(),
                    )
                    session.add(news)
                    added += 1

                except Exception as e:
                    errors += 1
                    logger.error(
                        f"Failed to save news '{news_data.get('title', '')[:30]}': {e}"
                    )
                    continue

            try:
                await session.commit()
                logger.info(
                    f"Database commit successful: added={added}, skipped={skipped}, errors={errors}"
                )
            except Exception as e:
                logger.error(f"Database commit failed: {e}")
                return 0

        # 清除缓存
        await self._clear_news_cache()

        logger.info(f"Synced {added} new news items")
        return added

    async def _clear_news_cache(self):
        """清除新闻相关缓存"""
        # 清除主要缓存键
        keys_to_clear = [
            self._cache_key("latest", "all", "all", "50"),
            self._cache_key("important", "3", "24", "20"),
            self._cache_key("market_news", "50"),
        ]
        for key in keys_to_clear:
            await self._delete_from_cache(key)

    async def process_news_with_llm(self, news_id: int) -> bool:
        """
        使用LLM处理单条新闻（生成摘要、分析情感、识别板块）
        :param news_id: 新闻ID
        :return: 是否处理成功
        """
        if not self.llm_client.is_configured():
            logger.warning("LLM not configured, skipping news processing")
            return False

        async with get_db_session() as session:
            result = await session.execute(select(News).where(News.id == news_id))
            news = result.scalar_one_or_none()

            if not news:
                logger.warning(f"News {news_id} not found")
                return False

            if news.is_processed:
                logger.debug(f"News {news_id} already processed")
                return True

            try:
                # 生成摘要
                content = news.content or news.title
                if content:
                    summary = self.llm_client.summarize_news(content)
                    if summary:
                        news.summary = summary

                    # 分析情感和相关板块
                    analysis = self.llm_client.analyze_news_sentiment(content)
                    if analysis:
                        news.sentiment = analysis.get("sentiment")
                        sectors = analysis.get("related_sectors", [])
                        if sectors:
                            news.related_sectors = ",".join(sectors)
                        if analysis.get("importance"):
                            news.importance = analysis.get("importance")

                news.is_processed = True
                news.updated_at = datetime.now()
                await session.commit()

                logger.info(f"Processed news {news_id} with LLM")
                return True

            except Exception as e:
                logger.error(f"Failed to process news {news_id}: {e}")
                return False

    async def process_unprocessed_news(self) -> int:
        """
        处理所有未处理的新闻（逐条处理，处理完一条立即更新数据库）
        :return: 处理成功的数量
        """
        if not self.llm_client.is_configured():
            logger.warning("LLM 未配置，跳过新闻处理")
            return 0

        async with get_db_session() as session:
            # 一次性获取所有未处理的新闻
            result = await session.execute(
                select(News)
                .where(
                    and_(
                        News.is_active == True,
                        News.is_processed == False,
                    )
                )
                .order_by(desc(News.publish_time))
            )
            news_list = result.scalars().all()

        total = len(news_list)
        if total == 0:
            return 0

        logger.info(f"[News] 发现 {total} 条未处理的新闻，开始处理...")

        processed = 0
        for i, news in enumerate(news_list, 1):
            if await self.process_news_with_llm(news.id):
                processed += 1
            # 每处理10条输出一次进度
            if i % 10 == 0:
                logger.info(f"[News] 处理进度: {i}/{total}")

        return processed

    async def generate_investment_recommendation(self) -> Optional[str]:
        """
        根据最新新闻生成投资建议
        :return: 投资建议文本
        """
        if not self.llm_client.is_configured():
            logger.warning("LLM not configured, cannot generate recommendation")
            return None

        # 获取最新重要新闻
        important_news = await self.get_important_news(
            min_importance=3, hours=24, limit=10
        )

        if not important_news:
            # 退而求其次，获取最新的市场新闻
            important_news = await self.get_market_news(limit=10)

        if not important_news:
            return "暂无足够的新闻数据生成投资建议"

        # 构建新闻列表
        news_list = [
            {
                "title": n.get("title", ""),
                "content": n.get("summary") or n.get("content", "")[:200],
                "source": n.get("source_name") or n.get("source", ""),
            }
            for n in important_news
        ]

        return self.llm_client.generate_investment_recommendation(news_list)

    def _news_to_dict(self, news: News) -> Dict[str, Any]:
        """将 News 模型转换为字典"""
        return {
            "id": news.id,
            "source": news.source,
            "source_name": news.source_name,
            "title": news.title,
            "content": news.content,
            "summary": news.summary,
            "url": news.url,
            "category": news.category,
            "tags": news.tags,
            "importance": news.importance,
            "related_sectors": news.related_sectors,
            "sentiment": news.sentiment,
            "publish_time": (
                news.publish_time.isoformat() if news.publish_time else None
            ),
            "is_processed": news.is_processed,
        }
