"""
股票 API 控制器
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from src.service.stock_service import StockService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stock", tags=["股票"])

# 服务实例
stock_service = StockService()


# ========== 请求/响应模型 ==========


class WatchlistAddRequest(BaseModel):
    code: str
    name: Optional[str] = None
    market: str = "CN"


class WatchlistRemoveRequest(BaseModel):
    code: str


# ========== API 接口 ==========


@router.get("/realtime")
async def get_realtime_quotes(
    codes: Optional[str] = Query(None, description="股票代码，逗号分隔"),
    limit: int = Query(50, description="返回数量限制"),
):
    """获取股票实时行情"""
    try:
        code_list = codes.split(",") if codes else None
        data = await stock_service.get_realtime_quotes(code_list)

        if not code_list:
            data = data[:limit]

        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get stock realtime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detail/{code}")
async def get_stock_detail(code: str):
    """获取股票详情"""
    try:
        data = await stock_service.get_stock_detail(code)
        if not data:
            raise HTTPException(status_code=404, detail="Stock not found")
        return {"code": 0, "data": data, "message": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stock detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{code}")
async def get_stock_history(
    code: str,
    period: str = Query("daily", description="周期 (daily/weekly/monthly)"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYYMMDD"),
):
    """获取股票历史数据"""
    try:
        data = await stock_service.get_stock_history(code, period, start_date, end_date)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get stock history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_stock(keyword: str = Query(..., description="搜索关键词")):
    """搜索股票"""
    try:
        data = await stock_service.search_stock(keyword)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to search stock: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 自选接口 ==========


@router.get("/watchlist")
async def get_watchlist(user_id: str = Query("default", description="用户ID")):
    """获取自选股列表"""
    try:
        data = await stock_service.get_watchlist(user_id)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watchlist")
async def add_to_watchlist(
    request: WatchlistAddRequest, user_id: str = Query("default", description="用户ID")
):
    """添加到自选"""
    try:
        data = await stock_service.add_to_watchlist(
            code=request.code, user_id=user_id, name=request.name, market=request.market
        )
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to add to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{code}")
async def remove_from_watchlist(
    code: str, user_id: str = Query("default", description="用户ID")
):
    """从自选移除"""
    try:
        result = await stock_service.remove_from_watchlist(code, user_id)
        if result:
            return {"code": 0, "data": None, "message": "success"}
        else:
            raise HTTPException(status_code=404, detail="Not in watchlist")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))
