"""
Agent API 控制器
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.agent import InvestmentAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["Agent"])


class ChatRequest(BaseModel):
    """对话请求"""

    message: str
    user_id: str = "default"
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """对话响应"""

    code: int
    message: str
    data: Optional[dict] = None


# Agent 实例缓存（简单实现，生产环境建议用 Redis）
_agent_cache: dict = {}


def _get_agent(user_id: str, session_id: str = None) -> InvestmentAgent:
    """获取或创建 Agent 实例"""
    cache_key = f"{user_id}:{session_id or 'default'}"
    if cache_key not in _agent_cache:
        _agent_cache[cache_key] = InvestmentAgent(
            user_id=user_id,
            session_id=session_id,
        )
    return _agent_cache[cache_key]


@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """与 Agent 对话"""
    try:
        agent = _get_agent(request.user_id, request.session_id)

        if not agent.is_configured():
            return ChatResponse(
                code=1,
                message="Agent 未配置，请设置 DASHSCOPE_API_KEY",
                data=None,
            )

        response = agent.chat(request.message)

        return ChatResponse(
            code=0,
            message="success",
            data={
                "response": response,
                "session_id": agent.session_id,
            },
        )

    except Exception as e:
        logger.error(f"Agent chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advice")
async def get_advice(
    topic: Optional[str] = Query(None, description="投资主题（如：新能源、军工）"),
    user_id: str = Query("default", description="用户ID"),
) -> ChatResponse:
    """获取投资建议"""
    try:
        agent = _get_agent(user_id)

        if not agent.is_configured():
            return ChatResponse(
                code=1,
                message="Agent 未配置，请设置 DASHSCOPE_API_KEY",
                data=None,
            )

        response = agent.get_investment_advice(topic)

        return ChatResponse(
            code=0,
            message="success",
            data={
                "advice": response,
                "topic": topic,
            },
        )

    except Exception as e:
        logger.error(f"Get advice error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def clear_session(
    user_id: str = Query("default", description="用户ID"),
    session_id: Optional[str] = Query(None, description="会话ID"),
) -> ChatResponse:
    """清除会话"""
    try:
        cache_key = f"{user_id}:{session_id or 'default'}"
        if cache_key in _agent_cache:
            _agent_cache[cache_key].clear_session()
            del _agent_cache[cache_key]

        return ChatResponse(
            code=0,
            message="Session cleared",
            data=None,
        )

    except Exception as e:
        logger.error(f"Clear session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status() -> ChatResponse:
    """获取 Agent 状态"""
    try:
        agent = InvestmentAgent()

        return ChatResponse(
            code=0,
            message="success",
            data={
                "configured": agent.is_configured(),
                "tools": list(agent.tools.keys()),
                "search_configured": agent.tools["web_search"].is_configured(),
            },
        )

    except Exception as e:
        logger.error(f"Get status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
