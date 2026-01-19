try:
    # 尝试导入Django模型
    from .gold import GoldIndex
    from .market import MarketIndex
    from .stock import StockQuote
except ImportError:
    # 如果失败，则导入Pydantic模型
    from .pydantic_models import GoldIndex, MarketIndex, StockQuote

__all__ = ["MarketIndex", "GoldIndex", "StockQuote"]
