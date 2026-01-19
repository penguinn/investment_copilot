"""
基金 API 控制器
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.service.fund_service import FundService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fund", tags=["基金"])

fund_service = FundService()


class WatchlistAddRequest(BaseModel):
    code: str
    name: Optional[str] = None
    fund_type: Optional[str] = None


@router.get("/summary")
async def get_fund_type_summary():
    """获取各类型基金的汇总统计数据"""
    try:
        data = await fund_service.get_fund_type_summary()
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get fund type summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/realtime")
async def get_realtime_navs(
    codes: Optional[str] = Query(None, description="基金代码，逗号分隔"),
    fund_type: Optional[str] = Query(None, description="基金类型"),
    limit: int = Query(50, description="返回数量限制")
):
    """获取基金实时净值"""
    try:
        code_list = codes.split(",") if codes else None
        data = await fund_service.get_realtime_navs(code_list, fund_type)
        
        if not code_list:
            data = data[:limit]
        
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get fund realtime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detail/{code}")
async def get_fund_detail(code: str):
    """获取基金详情"""
    try:
        data = await fund_service.get_fund_detail(code)
        if not data:
            raise HTTPException(status_code=404, detail="Fund not found")
        return {"code": 0, "data": data, "message": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get fund detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{code}")
async def get_fund_history(code: str):
    """获取基金历史净值"""
    try:
        data = await fund_service.get_fund_history(code)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get fund history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_fund(keyword: str = Query(..., description="搜索关键词")):
    """搜索基金"""
    try:
        data = await fund_service.search_fund(keyword)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to search fund: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist")
async def get_watchlist(user_id: str = Query("default")):
    """获取自选基金列表"""
    try:
        data = await fund_service.get_watchlist(user_id)
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
        data = await fund_service.add_to_watchlist(
            code=request.code,
            user_id=user_id,
            name=request.name,
            fund_type=request.fund_type
        )
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to add to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{code}")
async def remove_from_watchlist(code: str, user_id: str = Query("default")):
    """从自选移除"""
    try:
        result = await fund_service.remove_from_watchlist(code, user_id)
        if result:
            return {"code": 0, "data": None, "message": "success"}
        else:
            raise HTTPException(status_code=404, detail="Not in watchlist")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))
