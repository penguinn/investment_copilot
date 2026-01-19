"""
黄金 API 控制器
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.service.gold_service import GoldService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gold", tags=["黄金"])

gold_service = GoldService()


class WatchlistAddRequest(BaseModel):
    code: str
    name: Optional[str] = None


@router.get("/realtime")
async def get_realtime_prices():
    """获取黄金实时行情"""
    try:
        data = await gold_service.get_realtime_prices()
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get gold realtime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detail/{code}")
async def get_gold_detail(code: str):
    """获取黄金品种详情"""
    try:
        data = await gold_service.get_gold_detail(code)
        if not data:
            raise HTTPException(status_code=404, detail="Gold not found")
        return {"code": 0, "data": data, "message": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get gold detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{code}")
async def get_gold_history(
    code: str = "AU9999",
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """获取黄金历史数据"""
    try:
        data = await gold_service.get_gold_history(code, start_date, end_date)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get gold history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist")
async def get_watchlist(user_id: str = Query("default")):
    """获取自选黄金列表"""
    try:
        data = await gold_service.get_watchlist(user_id)
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
        data = await gold_service.add_to_watchlist(
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
        result = await gold_service.remove_from_watchlist(code, user_id)
        if result:
            return {"code": 0, "data": None, "message": "success"}
        else:
            raise HTTPException(status_code=404, detail="Not in watchlist")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))
