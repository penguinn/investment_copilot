"""
后台数据同步任务
定期从 AKShare 获取数据并存储到 Redis 和数据库
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

logger = logging.getLogger(__name__)


class DataSyncTask:
    """数据同步任务管理器"""

    def __init__(self):
        self._tasks: List[asyncio.Task] = []
        self._running = False
        # 用于同步各任务的状态
        self._daily_news_ready = asyncio.Event()
        self._daily_fund_ready = asyncio.Event()

    async def start(self):
        """启动所有同步任务"""
        if self._running:
            return

        self._running = True
        logger.info("Starting data sync tasks...")

        # 导入服务（延迟导入避免循环依赖）
        from src.service.fund_service import FundService
        from src.service.futures_service import FuturesService
        from src.service.gold_service import GoldService
        from src.service.market_service import MarketService
        from src.service.news_service import NewsService
        from src.service.stock_service import StockService

        # 创建服务实例
        market_service = MarketService()
        gold_service = GoldService()
        fund_service = FundService()
        futures_service = FuturesService()
        stock_service = StockService()
        news_service = NewsService()

        # 启动各个同步任务
        self._tasks = [
            asyncio.create_task(self._sync_market_data(market_service)),
            asyncio.create_task(self._sync_gold_data(gold_service)),
            asyncio.create_task(self._sync_futures_data(futures_service)),
            asyncio.create_task(self._sync_watchlist_data(stock_service)),
            asyncio.create_task(self._sync_etf_data(fund_service)),
            # 每日定时任务（14:00 执行）
            asyncio.create_task(self._daily_advice_task(news_service, fund_service)),
        ]

        logger.info(f"Started {len(self._tasks)} data sync tasks")

    async def stop(self):
        """停止所有同步任务"""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping data sync tasks...")

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []
        logger.info("All data sync tasks stopped")

    async def _sync_market_data(self, service):
        """同步市场指数数据"""
        indices = {
            "CN": ["SSE", "SZSE", "ChiNext"],
            "HK": ["HSI", "HSCEI", "HSTECH"],
            "US": ["DJI", "IXIC", "SPX"],
        }

        # 首次启动时预同步历史数据
        history_synced = False

        while self._running:
            try:
                for market, codes in indices.items():
                    for code in codes:
                        try:
                            # 获取数据并缓存（use_cache=False 强制刷新）
                            await service.get_market_data(
                                market=market,
                                symbol=code,
                                period="day",
                                use_cache=False,
                            )
                            logger.debug(f"Synced market data: {market}/{code}")
                        except Exception as e:
                            logger.warning(f"Failed to sync {market}/{code}: {e}")

                        # 每个请求间隔 1 秒，避免请求过快
                        await asyncio.sleep(1)

                # 首次启动时预同步历史数据（只同步一次，缓存1小时）
                if not history_synced:
                    await self._sync_market_history(service, indices)
                    history_synced = True

                logger.info("Market data sync completed")
            except Exception as e:
                logger.error(f"Market data sync error: {e}")

            # 每 30 秒同步一次
            await asyncio.sleep(30)

    async def _sync_market_history(self, service, indices):
        """同步市场指数历史数据（预热缓存）"""
        logger.info("Starting market history data sync (cache warmup)...")
        days_list = [7, 30, 90, 180, 365]  # 支持的时间范围

        for market, codes in indices.items():
            for code in codes:
                for days in days_list:
                    try:
                        # 使用 use_cache=False 强制刷新缓存
                        await service.get_index_history(
                            market=market,
                            symbol=code,
                            days=days,
                            use_cache=False,
                        )
                        logger.debug(f"Synced history: {market}/{code} ({days} days)")
                    except Exception as e:
                        logger.warning(
                            f"Failed to sync history {market}/{code}/{days}: {e}"
                        )

                    # 每个请求间隔 0.5 秒
                    await asyncio.sleep(0.5)

        logger.info("Market history data sync completed")

    async def _sync_gold_data(self, service):
        """同步黄金数据"""
        while self._running:
            try:
                await service.get_realtime_prices(use_cache=False)
                logger.info("Gold data sync completed")
            except Exception as e:
                logger.warning(f"Failed to sync gold data: {e}")

            # 每 30 秒同步一次
            await asyncio.sleep(30)

    async def _sync_futures_data(self, service):
        """同步期货数据"""
        while self._running:
            try:
                await service.get_realtime_quotes(use_cache=False)
                logger.info("Futures data sync completed")
            except Exception as e:
                logger.warning(f"Failed to sync futures data: {e}")

            # 每 30 秒同步一次
            await asyncio.sleep(30)

    async def _sync_watchlist_data(self, service):
        """同步自选股数据"""
        while self._running:
            try:
                # 获取所有用户的自选股并同步
                users = await service.get_all_watchlist_users()
                for user_id in users:
                    try:
                        await service.sync_watchlist_data(user_id)
                        logger.debug(f"Synced watchlist data for user: {user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to sync watchlist for {user_id}: {e}")

                    # 每个用户之间间隔 1 秒
                    await asyncio.sleep(1)

                logger.info("Watchlist data sync completed")
            except Exception as e:
                logger.warning(f"Failed to sync watchlist data: {e}")

            # 每 30 秒同步一次
            await asyncio.sleep(30)

    async def _sync_etf_data(self, service):
        """同步 ETF 数据（热门 ETF + 自选 ETF + 场外基金自选）"""
        # 首次启动时预热缓存
        etf_list_synced = False
        otc_list_synced = False

        while self._running:
            try:
                # 1. 同步热门 ETF 数据
                await service.get_hot_etfs(use_cache=False)
                logger.debug("Synced hot ETF data")

                # 2. 预热 ETF 列表（只同步一次，缓存1小时）
                if not etf_list_synced:
                    await service.get_etf_realtime(use_cache=False)
                    etf_list_synced = True
                    logger.info("ETF list cache warmed up")

                # 3. 预热场外基金列表（只同步一次，缓存5分钟）
                if not otc_list_synced:
                    await service.get_fund_ranking(use_cache=False)
                    otc_list_synced = True
                    logger.info("OTC fund list cache warmed up")

                # 4. 同步自选 ETF 数据
                await service.sync_etf_watchlist_data()

                # 5. 同步场外基金自选数据
                await service.sync_otc_watchlist_data()

                logger.info("ETF & OTC fund data sync completed")
            except Exception as e:
                logger.warning(f"Failed to sync ETF data: {e}")

            # 每 60 秒同步一次
            await asyncio.sleep(60)

    async def _daily_advice_task(self, news_service, fund_service):
        """
        每日投资建议任务（每天14:00执行）
        流程：
        1. 并行执行：新闻同步+LLM处理 | 基金数据同步
        2. Agent 生成投资建议
        3. 多渠道推送（日志/邮件/短信/数据库）
        """
        from src.agent import InvestmentAgent
        from src.config import DAILY_ADVICE_HOUR, DAILY_ADVICE_MINUTE
        from src.service.notification_service import NotificationService

        notification_service = NotificationService()
        first_run = True

        while self._running:
            try:
                # 首次启动时立即执行一次
                if first_run:
                    logger.info("[DailyAdvice] 应用启动，立即执行每日任务...")
                    await self._execute_daily_advice(
                        news_service, fund_service, notification_service
                    )
                    first_run = False

                now = datetime.now()
                # 计算下一次执行时间
                target_hour = DAILY_ADVICE_HOUR
                target_minute = DAILY_ADVICE_MINUTE

                next_run = now.replace(
                    hour=target_hour, minute=target_minute, second=0, microsecond=0
                )

                # 如果今天的时间已经过了，设置为明天
                if now >= next_run:
                    next_run = next_run + timedelta(days=1)

                wait_seconds = (next_run - now).total_seconds()

                logger.info(
                    f"[DailyAdvice] 下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')} "
                    f"(等待 {wait_seconds/3600:.1f} 小时)"
                )
                await asyncio.sleep(wait_seconds)

                # 执行每日任务
                await self._execute_daily_advice(
                    news_service, fund_service, notification_service
                )

            except Exception as e:
                logger.error(f"[DailyAdvice] 任务出错: {e}")
                # 发生错误时等待 5 分钟后重试
                await asyncio.sleep(300)

    async def _execute_daily_advice(self, news_service, fund_service, notification_service):
        """执行每日投资建议任务"""
        from src.agent import InvestmentAgent

        date_str = datetime.now().strftime("%Y年%m月%d日")
        logger.info(f"[DailyAdvice] ========== 开始执行 {date_str} 每日任务 ==========")

        # 步骤1: 并行执行【新闻同步+LLM处理】和【基金数据同步】
        logger.info("[DailyAdvice] 步骤1/3: 并行执行数据收集...")
        logger.info("[DailyAdvice]   ├─ 任务A: 新闻同步 + LLM处理")
        logger.info("[DailyAdvice]   └─ 任务B: 基金数据同步")

        # 并行执行两组任务
        news_result, fund_result = await asyncio.gather(
            self._sync_news_and_process(news_service),
            self._sync_fund_data_once(fund_service),
            return_exceptions=True,
        )

        # 处理结果
        if isinstance(news_result, Exception):
            logger.error(f"[DailyAdvice] 新闻任务失败: {news_result}")
        else:
            news_count, processed = news_result
            logger.info(f"[DailyAdvice] 任务A完成: 同步 {news_count} 条新闻，处理 {processed} 条")

        if isinstance(fund_result, Exception):
            logger.error(f"[DailyAdvice] 基金任务失败: {fund_result}")
        else:
            logger.info(f"[DailyAdvice] 任务B完成: 保存 {fund_result} 条基金数据")

        # 步骤2: Agent 生成投资建议
        logger.info("[DailyAdvice] 步骤2/3: Agent 生成投资建议...")
        advice = None
        try:
            agent = InvestmentAgent(user_id="daily_advice")
            if agent.is_configured():
                advice = agent.get_investment_advice()
                logger.info(f"[DailyAdvice] 投资建议生成成功，长度: {len(advice)} 字符")
            else:
                logger.warning("[DailyAdvice] Agent 未配置，跳过生成投资建议")
        except Exception as e:
            logger.error(f"[DailyAdvice] 生成投资建议失败: {e}")

        # 步骤3: 多渠道推送
        if advice:
            enabled_channels = notification_service.get_enabled_channels()
            logger.info(f"[DailyAdvice] 步骤3/3: 推送通知 (渠道: {', '.join(enabled_channels)})...")
            try:
                results = notification_service.send_investment_advice(advice, date_str)
                for channel, success in results.items():
                    status = "✅" if success else "❌"
                    logger.info(f"[DailyAdvice]   {status} {channel}")
            except Exception as e:
                logger.error(f"[DailyAdvice] 通知推送失败: {e}")
        else:
            logger.info("[DailyAdvice] 步骤3/3: 无投资建议，跳过推送")

        logger.info(f"[DailyAdvice] ========== {date_str} 每日任务完成 ==========")

    async def _sync_news_and_process(self, news_service):
        """同步新闻并用LLM处理（作为一个并行任务）"""
        # 同步新闻
        news_count = await news_service.sync_news()
        logger.info(f"[DailyAdvice]   ├─ 新闻同步完成: {news_count} 条")

        # LLM 处理
        processed = await news_service.process_unprocessed_news()
        logger.info(f"[DailyAdvice]   ├─ LLM处理完成: {processed} 条")

        return news_count, processed

    async def _sync_fund_data_once(self, fund_service):
        """同步基金数据一次（作为一个并行任务）"""
        fund_data = await fund_service.get_realtime_navs(use_cache=False)
        saved = 0
        if fund_data:
            saved = await fund_service.save_daily_navs(fund_data)
            logger.info(f"[DailyAdvice]   └─ 基金数据保存完成: {saved} 条")
        return saved


# 全局任务管理器实例
data_sync_task = DataSyncTask()
