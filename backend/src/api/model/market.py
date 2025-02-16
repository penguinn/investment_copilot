from django.db import models


class MarketIndex(models.Model):
    """市场指数模型"""

    MARKET_CHOICES = [
        ("CN", "China A-Share"),
        ("HK", "Hong Kong"),
        ("US", "United States"),
        ("GOLD", "Gold"),
    ]

    symbol = models.CharField(max_length=20)  # 指数代码
    market = models.CharField(max_length=10, choices=MARKET_CHOICES)  # 市场类型
    name = models.CharField(max_length=50)  # 指数名称
    time = models.DateTimeField()  # 时间戳
    open = models.DecimalField(max_digits=10, decimal_places=2)
    high = models.DecimalField(max_digits=10, decimal_places=2)
    low = models.DecimalField(max_digits=10, decimal_places=2)
    close = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField(null=True)  # 成交量，黄金指数可能没有
    change = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # 涨跌额
    change_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True
    )  # 涨跌幅

    class Meta:
        db_table = "market_index"
        indexes = [
            models.Index(fields=["symbol", "time"]),
            models.Index(fields=["market"]),
        ]
        unique_together = ("symbol", "time")

    def __str__(self):
        return f"{self.name} ({self.symbol})"
