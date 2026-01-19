import os
from typing import List

# 基础设置
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", "8080"))

# CORS设置
CORS_ALLOWED_ORIGINS: List[str] = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# PostgreSQL/TimescaleDB 配置
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_NAME = os.environ.get("DB_NAME", "stockdb")

# 构建数据库URL
DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
DATABASE_URL_SYNC = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# 缓存设置
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "redis123")
REDIS_DB = int(os.environ.get("REDIS_DB", "1"))
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
REDIS_TIMEOUT = 5
REDIS_RETRY = True

# 缓存过期时间（秒）
CACHE_TTL_REALTIME = 30  # 实时数据缓存30秒
CACHE_TTL_MINUTE = 60  # 分钟数据缓存1分钟
CACHE_TTL_DAILY = 300  # 日数据缓存5分钟
CACHE_TTL_HISTORY = 3600 * 24  # 历史数据缓存1天（历史数据不会变化）
CACHE_TTL_WATCHLIST = 3600 * 24  # 自选列表缓存1天

# 日志设置
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
