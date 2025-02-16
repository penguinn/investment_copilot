from django.db import models


class GoldIndex(models.Model):
    """黄金指数模型"""

    symbol = models.CharField(max_length=10, help_text="黄金代码")
    name = models.CharField(max_length=50, help_text="黄金名称")
    time = models.DateTimeField(help_text="时间")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="价格")
    open = models.DecimalField(max_digits=10, decimal_places=2, help_text="开盘价")
    high = models.DecimalField(max_digits=10, decimal_places=2, help_text="最高价")
    low = models.DecimalField(max_digits=10, decimal_places=2, help_text="最低价")
    close = models.DecimalField(max_digits=10, decimal_places=2, help_text="收盘价")
    change = models.DecimalField(max_digits=10, decimal_places=2, help_text="涨跌额")
    change_percent = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="涨跌幅"
    )

    class Meta:
        db_table = "gold_index"
        indexes = [
            models.Index(fields=["symbol", "time"]),
        ]
        unique_together = ("symbol", "time")

    def __str__(self):
        return f"{self.name} ({self.symbol})"
