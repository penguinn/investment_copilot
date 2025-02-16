from django.db import models


class MarketIndex(models.Model):
    """市场指数模型"""

    MARKET_CHOICES = [
        ("CN", "China A-Share"),
        ("HK", "Hong Kong"),
        ("US", "United States"),
        ("GOLD", "Gold"),
    ]

    symbol = models.CharField(max_length=10, help_text="指数代码")
    market = models.CharField(max_length=10, help_text="市场代码")
    name = models.CharField(max_length=50, help_text="指数名称")
    time = models.DateTimeField(help_text="时间")
    open = models.DecimalField(max_digits=10, decimal_places=2, help_text="开盘价")
    high = models.DecimalField(max_digits=10, decimal_places=2, help_text="最高价")
    low = models.DecimalField(max_digits=10, decimal_places=2, help_text="最低价")
    close = models.DecimalField(max_digits=10, decimal_places=2, help_text="收盘价")
    volume = models.DecimalField(max_digits=20, decimal_places=2, help_text="成交量")
    change = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 涨跌额
    change_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True
    )  # 涨跌幅

    class Meta:
        db_table = "market_index"
        indexes = [
            models.Index(fields=["market", "symbol", "time"]),
        ]
        unique_together = ("symbol", "time")

    def __str__(self):
        return f"{self.name} ({self.symbol})"
