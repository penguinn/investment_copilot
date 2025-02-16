import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseClient(ABC):
    """基础API客户端"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def request(self, *args, **kwargs) -> Dict[str, Any]:
        """发送请求"""
        pass

    def handle_error(self, error: Exception, context: Optional[Dict] = None) -> None:
        """统一错误处理"""
        error_context = context or {}
        self.logger.error(
            f"API request failed: {str(error)}", extra=error_context, exc_info=True
        )
