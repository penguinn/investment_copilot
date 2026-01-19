"""
后台数据同步任务
定期从 AKShare 获取数据并存储到 Redis 和数据库
"""
import asyncio
import logging
from datetime import datetime
from typing import Callable, List

logger = logging.getLogger(__name__)


class DataSyncTask:
    """数据同步任务管理器"""
    
    def __init__(self):
        self._tasks: List[asyncio.Task] = []
        self._running = False
    
    async def start(self):
        """启动所有同步任务"""
        if self._running:
            return
        
        self._running = True
        logger.info("Starting data sync tasks...")
        
        # 导入服务（延迟导入避免循环依赖）
        from src.service.market_service import MarketService
        from src.service.gold_service import GoldService
        from src.service.fund_service import FundService
        from src.service.futures_service import FuturesService
        
        # 创建服务实例
        market_service = MarketService()
        gold_service = GoldService()
        fund_service = FundService()
        futures_service = FuturesService()
        
        # 启动各个同步任务
        self._tasks = [
            asyncio.create_task(self._sync_market_data(market_service)),
            asyncio.create_task(self._sync_gold_data(gold_service)),
            asyncio.create_task(self._sync_fund_data(fund_service)),
            asyncio.create_task(self._sync_futures_data(futures_service)),
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
            'CN': ['SSE', 'SZSE', 'ChiNext'],
            'HK': ['HSI', 'HSCEI', 'HSTECH'],
            'US': ['DJI', 'IXIC', 'SPX'],
        }
        
        while self._running:
            try:
                for market, codes in indices.items():
                    for code in codes:
                        try:
                            # 获取数据并缓存（use_cache=False 强制刷新）
                            await service.get_market_data(
                                market=market,
                                symbol=code,
                                period='day',
                                use_cache=False
                            )
                            logger.debug(f"Synced market data: {market}/{code}")
                        except Exception as e:
                            logger.warning(f"Failed to sync {market}/{code}: {e}")
                        
                        # 每个请求间隔 1 秒，避免请求过快
                        await asyncio.sleep(1)
                
                logger.info("Market data sync completed")
            except Exception as e:
                logger.error(f"Market data sync error: {e}")
            
            # 每 30 秒同步一次
            await asyncio.sleep(30)
    
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
    
    async def _sync_fund_data(self, service):
        """同步基金数据"""
        while self._running:
            try:
                await service.get_realtime_navs(use_cache=False)
                logger.info("Fund data sync completed")
            except Exception as e:
                logger.warning(f"Failed to sync fund data: {e}")
            
            # 每 60 秒同步一次（基金数据更新频率较低）
            await asyncio.sleep(60)
    
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


# 全局任务管理器实例
data_sync_task = DataSyncTask()
