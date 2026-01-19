"""
外汇 API 控制器
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.service.forex_service import ForexService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/forex", tags=["外汇"])

forex_service = ForexService()


class WatchlistAddRequest(BaseModel):
    code: str
    name: Optional[str] = None


@router.get("/realtime")
async def get_realtime_quotes(
    category: Optional[str] = Query(None, description="分类 (cny/major/cross)")
):
    """获取外汇实时行情"""
    try:
        data = await forex_service.get_realtime_quotes(category)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get forex realtime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detail/{code}")
async def get_forex_detail(code: str):
    """获取货币对详情"""
    try:
        # URL 中的 / 需要编码，这里处理一下
        code = code.replace("-", "/")
        data = await forex_service.get_forex_detail(code)
        if not data:
            raise HTTPException(status_code=404, detail="Forex not found")
        return {"code": 0, "data": data, "message": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get forex detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{code}")
async def get_forex_history(
    code: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """获取外汇历史数据"""
    try:
        code = code.replace("-", "/")
        data = await forex_service.get_forex_history(code, start_date, end_date)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get forex history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist")
async def get_watchlist(user_id: str = Query("default")):
    """获取自选外汇列表"""
    try:
        data = await forex_service.get_watchlist(user_id)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watchlist")
async def add_to_watchlist(
    request: WatchlistAddRequest,
    user_id: str = Query("default")
):
    """添加到自选"""
    try:
        data = await forex_service.add_to_watchlist(
            code=request.code,
            user_id=user_id,
            name=request.name
        )
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to add to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{code}")
async def remove_from_watchlist(code: str, user_id: str = Query("default")):
    """从自选移除"""
    try:
        code = code.replace("-", "/")
        result = await forex_service.remove_from_watchlist(code, user_id)
        if result:
            return {"code": 0, "data": None, "message": "success"}
        else:
            raise HTTPException(status_code=404, detail="Not in watchlist")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))
