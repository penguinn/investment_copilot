"""
新闻 API 控制器
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.service.news_service import NewsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/news", tags=["新闻"])

news_service = NewsService()


@router.get("/latest")
async def get_latest_news(
    source: Optional[str] = Query(None, description="来源(cls/eastmoney/pbc/csrc/ndrc/stats/miit)"),
    category: Optional[str] = Query(None, description="分类(policy/news/data)"),
    limit: int = Query(50, description="返回数量"),
):
    """获取最新新闻"""
    try:
        data = await news_service.get_latest_news(source, category, limit)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get latest news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/important")
async def get_important_news(
    min_importance: int = Query(3, description="最小重要性(1-5)"),
    hours: int = Query(24, description="时间范围(小时)"),
    limit: int = Query(20, description="返回数量"),
):
    """获取重要新闻"""
    try:
        data = await news_service.get_important_news(min_importance, hours, limit)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get important news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policy")
async def get_policy_news(
    limit: int = Query(20, description="返回数量"),
):
    """获取政策新闻"""
    try:
        data = await news_service.get_policy_news(limit)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get policy news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market")
async def get_market_news(
    limit: int = Query(50, description="返回数量"),
):
    """获取市场快讯（财联社、东财）"""
    try:
        data = await news_service.get_market_news(limit)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get market news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_news(
    keyword: str = Query(..., description="搜索关键词"),
    limit: int = Query(50, description="返回数量"),
):
    """搜索新闻"""
    try:
        data = await news_service.search_news(keyword, limit)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to search news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sector/{sector}")
async def get_news_by_sector(
    sector: str,
    limit: int = Query(20, description="返回数量"),
):
    """获取某板块相关新闻"""
    try:
        data = await news_service.get_news_by_sector(sector, limit)
        return {"code": 0, "data": data, "message": "success"}
    except Exception as e:
        logger.error(f"Failed to get sector news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_news(
    source: Optional[str] = Query(None, description="指定来源，为空则同步所有"),
):
    """手动触发新闻同步（仅同步，不处理）"""
    try:
        count = await news_service.sync_news(source)
        return {"code": 0, "data": {"added": count}, "message": f"Synced {count} news items"}
    except Exception as e:
        logger.error(f"Failed to sync news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_news():
    """使用LLM处理所有未处理的新闻（生成摘要、分析情感）"""
    try:
        count = await news_service.process_unprocessed_news()
        return {"code": 0, "data": {"processed": count}, "message": f"处理完成，共 {count} 条"}
    except Exception as e:
        logger.error(f"Failed to process news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-and-process")
async def sync_and_process_news(
    source: Optional[str] = Query(None, description="指定来源，为空则同步所有"),
):
    """同步新闻并使用LLM处理（一键执行）"""
    try:
        # 步骤1: 同步新闻
        sync_count = await news_service.sync_news(source)
        logger.info(f"同步完成: {sync_count} 条")

        # 步骤2: 使用LLM处理所有未处理的新闻
        process_count = await news_service.process_unprocessed_news()
        logger.info(f"LLM处理完成: {process_count} 条")

        return {
            "code": 0,
            "data": {
                "synced": sync_count,
                "processed": process_count,
            },
            "message": f"同步 {sync_count} 条，处理 {process_count} 条",
        }
    except Exception as e:
        logger.error(f"Failed to sync and process news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendation")
async def get_investment_recommendation():
    """获取投资建议（基于最新新闻）"""
    try:
        recommendation = await news_service.generate_investment_recommendation()
        if recommendation:
            return {"code": 0, "data": {"recommendation": recommendation}, "message": "success"}
        else:
            return {"code": 1, "data": None, "message": "LLM not configured or no news available"}
    except Exception as e:
        logger.error(f"Failed to generate recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
