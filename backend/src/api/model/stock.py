from django.db import models


class StockQuote(models.Model):
    """股票报价模型"""

    symbol = models.CharField(max_length=20)
    time = models.DateTimeField(auto_now_add=True)
    current = models.DecimalField(max_digits=10, decimal_places=2)
    change = models.DecimalField(max_digits=10, decimal_places=2)
    change_percent = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        db_table = "stock_quote"
        indexes = [
            models.Index(fields=["symbol", "time"]),
        ]

    def __str__(self):
        return f"{self.symbol} @ {self.time}"
