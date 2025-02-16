from typing import Any, Dict

import akshare as ak

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

        # 获取上海黄金交易所数据
        try:
            sh_gold_df = ak.spot_goods_gold_sge()
            for symbol, info in gold_indices.items():
                if symbol == "AU9999":
                    gold_data[symbol] = {
                        "name": info["name"],
                        "price": float(
                            sh_gold_df.loc[
                                sh_gold_df["品种"] == "Au99.99", "最新价"
                            ].iloc[0]
                        ),
                        "change": float(
                            sh_gold_df.loc[
                                sh_gold_df["品种"] == "Au99.99", "涨跌"
                            ].iloc[0]
                        ),
                        "change_percent": float(
                            sh_gold_df.loc[
                                sh_gold_df["品种"] == "Au99.99", "涨跌幅"
                            ].iloc[0]
                        ),
                    }
        except Exception as e:
            self.handle_error(e, {"source": "SGE", "symbol": "AU9999"})

        # 获取伦敦金数据
        try:
            london_gold_df = ak.spot_goods_gold_london()
            if "XAU" in gold_indices:
                gold_data["XAU"] = {
                    "name": gold_indices["XAU"]["name"],
                    "price": float(london_gold_df["美元价格"].iloc[0]),
                    "change": float(london_gold_df["涨跌"].iloc[0]),
                    "change_percent": float(london_gold_df["涨跌幅"].iloc[0]),
                }
        except Exception as e:
            self.handle_error(e, {"source": "London", "symbol": "XAU"})

        return gold_data
