from typing import Any, Dict, List, Optional

from .cache import BaseCache


class MarketCache(BaseCache):
    """市场数据缓存"""

    def __init__(self):
        super().__init__("market")

    async def get_latest(self, market: str, symbol: str) -> Optional[Dict[str, Any]]:
        """获取最新市场数据"""
        return await self.get(f"{market}:{symbol}:latest")

    async def set_latest(self, market: str, symbol: str, data: Dict[str, Any]) -> None:
        """设置最新市场数据"""
        await self.set(f"{market}:{symbol}:latest", data, timeout=60)

    async def get_history(
        self, market: str, symbol: str, start_time: str, end_time: str
    ) -> Optional[List[Dict[str, Any]]]:
        """获取历史数据"""
        return await self.get(f"{market}:{symbol}:history:{start_time}:{end_time}")

    async def set_history(
        self,
        market: str,
        symbol: str,
        start_time: str,
        end_time: str,
        data: List[Dict[str, Any]],
    ) -> None:
        """设置历史数据"""
        await self.set(
            f"{market}:{symbol}:history:{start_time}:{end_time}", data, timeout=300
        )
