"""
债券 API 控制器
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.service.bond_service import BondService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bond", tags=["债券"])

bond_service = BondService()


class WatchlistAddRequest(BaseModel):
    code: str
    name: Optional[str] = None
    bond_type: Optional[str] = None


@router.get("/treasury-yields")
async def get_treasury_yields():
    """获取国债收益率"""
    try:
        data = await bond_service.get_treasury_yields()
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get treasury yields: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/realtime")
async def get_realtime_quotes(
    bond_type: Optional[str] = Query(None, description="债券类型 (treasury/corporate/convertible)")
):
    """获取债券实时行情"""
    try:
        data = await bond_service.get_realtime_quotes(bond_type)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get bond realtime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detail/{code}")
async def get_bond_detail(code: str):
    """获取债券详情"""
    try:
        data = await bond_service.get_bond_detail(code)
        if not data:
            raise HTTPException(status_code=404, detail="Bond not found")
        return {"code": 0, "data": data, "message": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bond detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_bond(keyword: str = Query(..., description="搜索关键词")):
    """搜索债券"""
    try:
        data = await bond_service.search_bond(keyword)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to search bond: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist")
async def get_watchlist(user_id: str = Query("default")):
    """获取自选债券列表"""
    try:
        data = await bond_service.get_watchlist(user_id)
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
        data = await bond_service.add_to_watchlist(
            code=request.code,
            user_id=user_id,
            name=request.name,
            bond_type=request.bond_type
        )
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to add to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{code}")
async def remove_from_watchlist(code: str, user_id: str = Query("default")):
    """从自选移除"""
    try:
        result = await bond_service.remove_from_watchlist(code, user_id)
        if result:
            return {"code": 0, "data": None, "message": "success"}
        else:
            raise HTTPException(status_code=404, detail="Not in watchlist")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))
