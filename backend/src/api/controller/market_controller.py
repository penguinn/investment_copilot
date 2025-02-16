import json
import logging
from datetime import datetime

from django.core.cache import cache
from django.http import JsonResponse
from rest_framework.decorators import api_view

from ...service.market_service import MarketService

logger = logging.getLogger(__name__)

# 市场指数配置
MARKET_INDICES = {
    # A股市场
    "CN": {
        "SSE": {"symbol": "sh000001", "name": "上证指数"},
        "SZSE": {"symbol": "sz399001", "name": "深证成指"},
        "ChiNext": {"symbol": "sz399006", "name": "创业板指"},
    },
    # 港股市场
    "HK": {
        "HSI": {"symbol": "hkHSI", "name": "恒生指数"},
        "HSCEI": {"symbol": "hkHSCEI", "name": "恒生国企指数"},
        "HSTECH": {"symbol": "hkHSTECH", "name": "恒生科技指数"},
    },
    # 美股市场
    "US": {
        "DJI": {"symbol": "DJI", "name": "道琼斯工业指数"},
        "IXIC": {"symbol": "IXIC", "name": "纳斯达克综合指数"},
        "SPX": {"symbol": "SPX", "name": "标普500指数"},
    },
}

# 创建服务实例
market_service = MarketService()


@api_view(["GET"])
async def market_index(request, market: str, index_code: str):
    """
    获取指定市场的指数数据
    :param market: 市场代码 (CN/HK/US)
    :param index_code: 指数代码
    :query chart_type: 图表类型 (kline/trend)
    :query period: 时间周期 (1min/5min/15min/30min/60min/day/week/month)
    :query start_time: 开始时间
    :query end_time: 结束时间
    """
    try:
        # 获取请求参数
        chart_type = request.GET.get("chart_type", "kline")  # kline 或 trend
        period = request.GET.get("period", "day")  # 默认日K
        start_time = request.GET.get("start_time")
        end_time = request.GET.get("end_time")

        # 验证参数
        if chart_type not in ["kline", "trend"]:
            return JsonResponse(
                {"code": 1, "message": "Invalid chart type"}, status=400
            )

        if period not in [
            "1min",
            "5min",
            "15min",
            "30min",
            "60min",
            "day",
            "week",
            "month",
        ]:
            return JsonResponse({"code": 1, "message": "Invalid period"}, status=400)

        if market not in MARKET_INDICES:
            return JsonResponse({"code": 1, "message": "Invalid market"}, status=400)

        # 获取市场指数信息
        market_info = MARKET_INDICES[market]
        if index_code not in market_info:
            return JsonResponse(
                {"code": 1, "message": "Invalid index code"}, status=400
            )

        index_info = market_info[index_code]
        symbol = index_info["symbol"]

        # 根据图表类型获取数据
        if chart_type == "kline":
            if start_time and end_time:
                # 获取历史数据
                data = await market_service.get_market_history(
                    market=market,
                    symbol=symbol,
                    start_time=start_time,
                    end_time=end_time,
                )
            else:
                # 获取最新数据
                data = await market_service.get_market_data(
                    market=market, symbol=symbol, period=period
                )
        else:  # trend
            if not (start_time and end_time):
                return JsonResponse(
                    {
                        "code": 1,
                        "message": "start_time and end_time are required for trend chart",
                    },
                    status=400,
                )
            # 获取趋势数据
            data = await market_service.get_market_trend(
                market=market,
                symbol=symbol,
                start_time=start_time,
                end_time=end_time,
                interval=period,
            )

        return JsonResponse(
            {
                "code": 0,
                "data": {
                    "market": market,
                    "symbol": symbol,
                    "name": index_info["name"],
                    "items": data,
                },
            }
        )

    except Exception as e:
        logger.error(f"Failed to get market index: {str(e)}", exc_info=True)
        return JsonResponse(
            {"code": 1, "message": f"获取市场指数失败: {str(e)}"}, status=500
        )
