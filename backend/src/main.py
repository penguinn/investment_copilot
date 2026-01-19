"""
Investment Copilot API 主应用
"""
import logging
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import CORS_ALLOWED_ORIGINS, LOG_FORMAT, LOG_LEVEL, API_HOST, API_PORT
from src.api.controller.stock_controller import router as stock_router
from src.api.controller.fund_controller import router as fund_router
from src.api.controller.gold_controller import router as gold_router
from src.api.controller.futures_controller import router as futures_router
from src.api.controller.bond_controller import router as bond_router
from src.api.controller.forex_controller import router as forex_router
from src.api.controller.market_controller import router as market_router
from src.infrastructure.db.database import init_db, close_db
from src.tasks import data_sync_task

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    logger.info("Initializing database...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
    
    # 启动后台数据同步任务
    logger.info("Starting background data sync tasks...")
    try:
        await data_sync_task.start()
        logger.info("Background tasks started successfully")
    except Exception as e:
        logger.warning(f"Failed to start background tasks: {e}")
    
    yield
    
    # 停止后台任务
    logger.info("Stopping background tasks...")
    await data_sync_task.stop()
    
    # 关闭数据库连接
    logger.info("Closing database connection...")
    await close_db()


# 创建FastAPI应用
app = FastAPI(
    title="Investment Copilot API",
    description="投资助手 API 接口",
    version="2.0.0",
    lifespan=lifespan,
)

# 请求耗时中间件
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # 转换为毫秒
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}ms")
        return response

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加耗时中间件
app.add_middleware(TimingMiddleware)

# 注册路由
app.include_router(stock_router)
app.include_router(fund_router)
app.include_router(gold_router)
app.include_router(futures_router)
app.include_router(bond_router)
app.include_router(forex_router)
app.include_router(market_router)


@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "Welcome to Investment Copilot API",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


# 启动应用的入口点
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )
