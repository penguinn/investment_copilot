import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from src.service.market_service import MarketService

logger = logging.getLogger(__name__)

# 市场指数配置
MARKET_INDICES = {
    # A股市场
    "CN": {
        "SSE": {"name": "上证指数"},
        "SZSE": {"name": "深证成指"},
        "ChiNext": {"name": "创业板指"},
    },
    # 港股市场
    "HK": {
        "HSI": {"name": "恒生指数"},
        "HSCEI": {"name": "恒生国企指数"},
        "HSTECH": {"name": "恒生科技指数"},
    },
    # 美股市场
    "US": {
        "DJI": {"name": "道琼斯"},
        "IXIC": {"name": "纳斯达克"},
        "SPX": {"name": "标普500"},
    },
}

# 创建路由器
router = APIRouter(prefix="/api", tags=["市场指数"])

# 创建服务实例
market_service = MarketService()


@router.get("/market/{market}/{index_code}/history")
async def market_index_history(
    market: str,
    index_code: str,
    days: int = Query(30, description="获取天数，默认30天"),
):
    """
    获取指数历史数据（用于折线图）
    :param market: 市场代码 (CN/HK/US)
    :param index_code: 指数代码
    :param days: 获取天数
    """
    try:
        if market not in MARKET_INDICES:
            raise HTTPException(status_code=400, detail="Invalid market")

        market_info = MARKET_INDICES[market]
        if index_code not in market_info:
            raise HTTPException(status_code=400, detail="Invalid index code")

        index_info = market_info[index_code]

        # 获取历史数据
        data = await market_service.get_index_history(
            market=market, symbol=index_code, days=days
        )

        return {
            "code": 0,
            "data": data,
            "message": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get market index history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取指数历史数据失败: {str(e)}")


@router.get("/market/{market}/{index_code}")
async def market_index(
    market: str,
    index_code: str,
    chart_type: str = Query("kline", description="图表类型 (kline/trend)"),
    period: str = Query(
        "day", description="时间周期 (1min/5min/15min/30min/60min/day/week/month)"
    ),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
):
    """
    获取指定市场的指数数据
    :param market: 市场代码 (CN/HK/US)
    :param index_code: 指数代码
    :param chart_type: 图表类型 (kline/trend)
    :param period: 时间周期 (1min/5min/15min/30min/60min/day/week/month)
    :param start_time: 开始时间
    :param end_time: 结束时间
    """
    try:
        # 验证参数
        if chart_type not in ["kline", "trend"]:
            raise HTTPException(status_code=400, detail="Invalid chart type")

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
            raise HTTPException(status_code=400, detail="Invalid period")

        if market not in MARKET_INDICES:
            raise HTTPException(status_code=400, detail="Invalid market")

        # 获取市场指数信息
        market_info = MARKET_INDICES[market]
        if index_code not in market_info:
            raise HTTPException(status_code=400, detail="Invalid index code")

        index_info = market_info[index_code]

        # 根据图表类型获取数据
        if chart_type == "kline":
            if start_time and end_time:
                # 获取历史数据
                data = await market_service.get_market_history(
                    market=market,
                    symbol=index_code,
                    start_time=start_time,
                    end_time=end_time,
                )
            else:
                # 获取最新数据
                data = await market_service.get_market_data(
                    market=market, symbol=index_code, period=period
                )
        else:  # trend
            if not (start_time and end_time):
                raise HTTPException(
                    status_code=400,
                    detail="start_time and end_time are required for trend chart",
                )
            # 获取趋势数据
            data = await market_service.get_market_trend(
                market=market,
                symbol=index_code,
                start_time=start_time,
                end_time=end_time,
                interval=period,
            )

        return {
            "code": 0,
            "data": {
                "market": market,
                "symbol": index_code,
                "name": index_info["name"],
                "items": data,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get market index: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取市场指数失败: {str(e)}")
