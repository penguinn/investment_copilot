"""
数据库初始化脚本
创建表结构和 TimescaleDB hypertables
"""
import asyncio
import logging

from sqlalchemy import text

from src.infrastructure.db.database import async_engine, Base
from src.infrastructure.db.models import (
    Stock, StockQuote, StockWatchlist,
    Fund, FundNav, FundWatchlist,
    Gold, GoldPrice, GoldWatchlist,
    Futures, FuturesQuote, FuturesWatchlist,
    Bond, BondQuote, BondWatchlist,
    Forex, ForexQuote, ForexWatchlist,
    MarketIndex, MarketIndexQuote,
)
from src.infrastructure.db.models.bond import TreasuryYield

logger = logging.getLogger(__name__)

# 需要转换为 hypertable 的时序表
HYPERTABLES = [
    ("stock_quotes", "time"),
    ("fund_navs", "time"),
    ("gold_prices", "time"),
    ("futures_quotes", "time"),
    ("bond_quotes", "time"),
    ("treasury_yields", "time"),
    ("forex_quotes", "time"),
    ("market_index_quotes", "time"),
]


async def create_hypertables():
    """创建 TimescaleDB hypertables"""
    async with async_engine.begin() as conn:
        for table_name, time_column in HYPERTABLES:
            try:
                # 检查表是否已经是 hypertable
                result = await conn.execute(
                    text(f"""
                        SELECT * FROM timescaledb_information.hypertables 
                        WHERE hypertable_name = '{table_name}'
                    """)
                )
                if result.fetchone():
                    logger.info(f"Table {table_name} is already a hypertable")
                    continue

                # 转换为 hypertable
                await conn.execute(
                    text(f"""
                        SELECT create_hypertable(
                            '{table_name}', 
                            '{time_column}',
                            if_not_exists => TRUE,
                            migrate_data => TRUE
                        )
                    """)
                )
                logger.info(f"Created hypertable for {table_name}")

                # 设置压缩策略（可选，7天后自动压缩）
                await conn.execute(
                    text(f"""
                        ALTER TABLE {table_name} SET (
                            timescaledb.compress,
                            timescaledb.compress_segmentby = 'code'
                        )
                    """)
                )
                
                # 添加压缩策略
                await conn.execute(
                    text(f"""
                        SELECT add_compression_policy('{table_name}', INTERVAL '7 days', if_not_exists => TRUE)
                    """)
                )
                logger.info(f"Enabled compression for {table_name}")

            except Exception as e:
                logger.warning(f"Failed to create hypertable for {table_name}: {e}")


async def init_database():
    """初始化数据库"""
    async with async_engine.begin() as conn:
        # 1. 启用 TimescaleDB 扩展
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE"))
        logger.info("TimescaleDB extension enabled")

        # 2. 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        logger.info("All tables created")

    # 3. 创建 hypertables
    await create_hypertables()
    logger.info("Database initialization completed")


async def drop_all_tables():
    """删除所有表（危险操作，仅用于开发）"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("All tables dropped")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_database())
