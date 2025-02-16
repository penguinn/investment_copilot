from datetime import datetime
from typing import Any, Dict

import akshare as ak
import pytz

from ..base import BaseClient


class GoldClient(BaseClient):
    """黄金数据客户端"""

    async def request(self, *args, **kwargs) -> Dict[str, Any]:
        """实现基类的request方法"""
        return self.get_gold_data(*args, **kwargs)

    def get_gold_data(
        self, gold_indices: Dict[str, Dict[str, str]]
    ) -> Dict[str, Dict[str, Any]]:
        """获取黄金数据"""
        gold_data = {}
        current_time = datetime.now(pytz.timezone("Asia/Shanghai")).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # 获取上海黄金交易所数据
        try:
            # 使用上海期货交易所黄金期货数据
            sh_gold_df = ak.futures_main_sina("AU0")  # 黄金期货主力合约
            if "AU9999" in gold_indices and not sh_gold_df.empty:
                # 打印列名以便调试
                print("上海期货交易所数据列名:", sh_gold_df.columns.tolist())
                gold_data["AU9999"] = {
                    "symbol": "AU9999",
                    "name": gold_indices["AU9999"]["name"],
                    "time": current_time,
                    "price": float(sh_gold_df["收盘价"].iloc[-1]),
                    "change": float(
                        sh_gold_df["收盘价"].iloc[-1] - sh_gold_df["开盘价"].iloc[-1]
                    ),
                    "change_percent": float(
                        (sh_gold_df["收盘价"].iloc[-1] - sh_gold_df["开盘价"].iloc[-1])
                        / sh_gold_df["开盘价"].iloc[-1]
                        * 100
                    ),
                }
        except Exception as e:
            self.handle_error(e, {"source": "SGE", "symbol": "AU9999"})

        # 获取COMEX黄金期货数据
        try:
            # 使用COMEX黄金期货主力合约数据
            us_gold_df = ak.futures_foreign_hist(symbol="GC")
            if "XAU" in gold_indices and not us_gold_df.empty:
                # 打印列名以便调试
                print("COMEX期货数据列名:", us_gold_df.columns.tolist())
                latest_data = us_gold_df.iloc[-1]
                gold_data["XAU"] = {
                    "symbol": "XAU",
                    "name": gold_indices["XAU"]["name"],
                    "time": current_time,
                    "price": float(latest_data["close"]),
                    "change": float(latest_data["close"] - latest_data["open"]),
                    "change_percent": float(
                        (latest_data["close"] - latest_data["open"])
                        / latest_data["open"]
                        * 100
                    ),
                }
        except Exception as e:
            self.handle_error(e, {"source": "COMEX", "symbol": "XAU"})

        return gold_data
