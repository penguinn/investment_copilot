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


# ==================== 场外基金排行榜和详情 ====================


@router.get("/otc/ranking")
async def get_fund_ranking(
    fund_type: Optional[str] = Query(None, description="基金类型（股票型/混合型/债券型/指数型/QDII）"),
    sort_by: str = Query("return_1y", description="排序字段（return_1w/return_1m/return_3m/return_6m/return_1y/return_ytd）"),
    limit: int = Query(20, description="返回数量"),
):
    """获取场外基金排行榜"""
    try:
        data = await fund_service.get_fund_ranking(fund_type, sort_by, limit)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get fund ranking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/otc/detail/{code}")
async def get_fund_detail_full(code: str):
    """获取场外基金完整详情（含历史净值走势）"""
    try:
        data = await fund_service.get_fund_detail_full(code)
        if not data:
            raise HTTPException(status_code=404, detail="Fund not found")
        return {"code": 0, "data": data, "message": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get fund detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/otc/search")
async def search_otc_fund(keyword: str = Query(..., description="搜索关键词")):
    """搜索场外基金"""
    try:
        data = await fund_service.search_otc_fund(keyword)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to search OTC fund: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/otc/watchlist")
async def get_otc_watchlist(
    user_id: str = Query("default"),
    refresh: bool = Query(False, description="是否强制刷新"),
):
    """获取场外基金自选列表"""
    try:
        data = await fund_service.get_otc_watchlist(user_id, use_cache=not refresh)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get OTC watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/otc/watchlist")
async def add_otc_to_watchlist(
    request: WatchlistAddRequest,
    user_id: str = Query("default"),
):
    """添加场外基金到自选"""
    try:
        data = await fund_service.add_otc_to_watchlist(
            code=request.code,
            user_id=user_id,
            name=request.name,
            fund_type=request.fund_type,
        )
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to add OTC fund to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/otc/watchlist/{code}")
async def remove_otc_from_watchlist(
    code: str,
    user_id: str = Query("default"),
):
    """从场外基金自选移除"""
    try:
        result = await fund_service.remove_otc_from_watchlist(code, user_id)
        if result:
            return {"code": 0, "data": None, "message": "success"}
        else:
            raise HTTPException(status_code=404, detail="Not in watchlist")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove OTC fund from watchlist: {e}")
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


# ==================== 场内基金（ETF）API ====================


class ETFWatchlistAddRequest(BaseModel):
    code: str
    name: Optional[str] = None


@router.get("/etf/realtime")
async def get_etf_realtime(
    codes: Optional[str] = Query(None, description="ETF代码，逗号分隔"),
    etf_type: Optional[str] = Query(None, description="ETF类型"),
    limit: int = Query(100, description="返回数量限制"),
):
    """获取 ETF 实时行情"""
    try:
        code_list = codes.split(",") if codes else None
        data = await fund_service.get_etf_realtime(code_list, etf_type)

        if not code_list:
            data = data[:limit]

        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get ETF realtime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/etf/history/{code}")
async def get_etf_history(
    code: str,
    days: int = Query(30, description="天数"),
):
    """获取 ETF 历史数据"""
    try:
        data = await fund_service.get_etf_history(code, days)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get ETF history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/etf/search")
async def search_etf(keyword: str = Query(..., description="搜索关键词")):
    """搜索 ETF"""
    try:
        data = await fund_service.search_etf(keyword)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to search ETF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/etf/hot")
async def get_hot_etfs():
    """获取热门 ETF"""
    try:
        data = await fund_service.get_hot_etfs()
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get hot ETFs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/etf/watchlist")
async def get_etf_watchlist(
    user_id: str = Query("default"),
    refresh: bool = Query(False, description="是否强制刷新"),
):
    """获取 ETF 自选列表"""
    try:
        data = await fund_service.get_etf_watchlist(user_id, use_cache=not refresh)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get ETF watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/etf/watchlist")
async def add_etf_to_watchlist(
    request: ETFWatchlistAddRequest,
    user_id: str = Query("default"),
):
    """添加 ETF 到自选"""
    try:
        data = await fund_service.add_etf_to_watchlist(
            code=request.code,
            user_id=user_id,
            name=request.name,
        )
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to add ETF to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/etf/watchlist/{code}")
async def remove_etf_from_watchlist(
    code: str,
    user_id: str = Query("default"),
):
    """从 ETF 自选移除"""
    try:
        result = await fund_service.remove_etf_from_watchlist(code, user_id)
        if result:
            return {"code": 0, "data": None, "message": "success"}
        else:
            raise HTTPException(status_code=404, detail="Not in watchlist")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove ETF from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))
