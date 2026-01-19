"""
期货 API 控制器
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.service.futures_service import FuturesService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/futures", tags=["期货"])

futures_service = FuturesService()


class WatchlistAddRequest(BaseModel):
    code: str
    name: Optional[str] = None
    category: Optional[str] = None


@router.get("/realtime")
async def get_realtime_quotes(
    category: Optional[str] = Query(None, description="分类 (index/bond/commodity)")
):
    """获取期货实时行情"""
    try:
        data = await futures_service.get_realtime_quotes(category)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get futures realtime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/main-contracts")
async def get_main_contracts():
    """获取主力合约列表"""
    try:
        data = await futures_service.get_main_contracts()
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get main contracts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detail/{code}")
async def get_futures_detail(code: str):
    """获取期货合约详情"""
    try:
        data = await futures_service.get_futures_detail(code)
        if not data:
            raise HTTPException(status_code=404, detail="Futures not found")
        return {"code": 0, "data": data, "message": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get futures detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{code}")
async def get_futures_history(
    code: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """获取期货历史数据"""
    try:
        data = await futures_service.get_futures_history(code, start_date, end_date)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get futures history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist")
async def get_watchlist(user_id: str = Query("default")):
    """获取自选期货列表"""
    try:
        data = await futures_service.get_watchlist(user_id)
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
        data = await futures_service.add_to_watchlist(
            code=request.code,
            user_id=user_id,
            name=request.name,
            category=request.category
        )
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to add to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{code}")
async def remove_from_watchlist(code: str, user_id: str = Query("default")):
    """从自选移除"""
    try:
        result = await futures_service.remove_from_watchlist(code, user_id)
        if result:
            return {"code": 0, "data": None, "message": "success"}
        else:
            raise HTTPException(status_code=404, detail="Not in watchlist")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))
