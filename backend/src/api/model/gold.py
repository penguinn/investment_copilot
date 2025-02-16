from django.db import models


class GoldIndex(models.Model):
    """黄金指数模型"""

    symbol = models.CharField(max_length=20)  # 黄金品种代码
    name = models.CharField(max_length=50)  # 品种名称
    time = models.DateTimeField()  # 时间戳
    price = models.DecimalField(max_digits=10, decimal_places=2)  # 当前价格
    open = models.DecimalField(max_digits=10, decimal_places=2)
    high = models.DecimalField(max_digits=10, decimal_places=2)
    low = models.DecimalField(max_digits=10, decimal_places=2)
    close = models.DecimalField(max_digits=10, decimal_places=2)
    change = models.DecimalField(max_digits=10, decimal_places=2)  # 涨跌额
    change_percent = models.DecimalField(max_digits=5, decimal_places=2)  # 涨跌幅

    class Meta:
        db_table = "gold_index"
        indexes = [
            models.Index(fields=["symbol", "time"]),
        ]
        unique_together = ("symbol", "time")

    def __str__(self):
        return f"{self.name} ({self.symbol})"
