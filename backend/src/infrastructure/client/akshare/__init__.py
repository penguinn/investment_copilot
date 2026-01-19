from src.infrastructure.client.akshare.stock import StockClient
from src.infrastructure.client.akshare.fund import FundClient
from src.infrastructure.client.akshare.gold import GoldClient
from src.infrastructure.client.akshare.futures import FuturesClient
from src.infrastructure.client.akshare.bond import BondClient
from src.infrastructure.client.akshare.forex import ForexClient
from src.infrastructure.client.akshare.market import MarketClient

__all__ = [
    "StockClient",
    "FundClient",
    "GoldClient",
    "FuturesClient",
    "BondClient",
    "ForexClient",
    "MarketClient",
]
