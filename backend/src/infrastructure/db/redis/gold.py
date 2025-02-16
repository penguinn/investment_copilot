from typing import Any, Dict, List, Optional

from .cache import BaseCache


class GoldCache(BaseCache):
    """黄金数据缓存"""

    def __init__(self):
        super().__init__("gold")

    async def get_latest(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取最新黄金数据"""
        return await self.get(f"{symbol}:latest")

    async def set_latest(self, symbol: str, data: Dict[str, Any]) -> None:
        """设置最新黄金数据"""
        await self.set(f"{symbol}:latest", data, timeout=60)

    async def get_history(
        self, symbol: str, start_time: str, end_time: str
    ) -> Optional[List[Dict[str, Any]]]:
        """获取历史数据"""
        return await self.get(f"{symbol}:history:{start_time}:{end_time}")

    async def set_history(
        self, symbol: str, start_time: str, end_time: str, data: List[Dict[str, Any]]
    ) -> None:
        """设置历史数据"""
        await self.set(f"{symbol}:history:{start_time}:{end_time}", data, timeout=300)
