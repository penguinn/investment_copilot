"""
Agent 工具基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """工具基类"""

    name: str = ""
    description: str = ""

    @abstractmethod
    def run(self, **kwargs) -> str:
        """
        执行工具
        :param kwargs: 工具参数
        :return: 工具执行结果（字符串）
        """
        pass

    def to_schema(self) -> Dict[str, Any]:
        """
        转换为 OpenAI function calling 格式
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters(),
            },
        }

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """
        获取工具参数 schema
        """
        pass
