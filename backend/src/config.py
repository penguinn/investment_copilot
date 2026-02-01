import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

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

# 阿里百炼平台配置
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
DASHSCOPE_MODEL = os.environ.get("DASHSCOPE_MODEL", "qwen-turbo")
DASHSCOPE_MODEL_SUMMARY = os.environ.get(
    "DASHSCOPE_MODEL_SUMMARY", "qwen-plus"
)  # 新闻摘要
DASHSCOPE_MODEL_AGENT = os.environ.get("DASHSCOPE_MODEL_AGENT", "qwen-max")  # Agent推理

# 搜索工具配置
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY", "")

# 新闻同步配置
NEWS_SYNC_HOURS = int(os.environ.get("NEWS_SYNC_HOURS", "24"))  # 同步最近多少小时的新闻

# 每日投资建议配置
DAILY_ADVICE_HOUR = int(
    os.environ.get("DAILY_ADVICE_HOUR", "14")
)  # 每天执行时间（小时）
DAILY_ADVICE_MINUTE = int(
    os.environ.get("DAILY_ADVICE_MINUTE", "0")
)  # 每天执行时间（分钟）

# 通知渠道配置（可多选，逗号分隔）
# 可选值: log, email, sms, database
# 例如: "log,email" 表示同时输出日志和发送邮件
NOTIFY_CHANNELS = os.environ.get("NOTIFY_CHANNELS", "log,database")

# 邮件配置（当 NOTIFY_CHANNELS 包含 email 时生效）
EMAIL_ENABLED = os.environ.get("EMAIL_ENABLED", "false").lower() == "true"
EMAIL_SMTP_HOST = os.environ.get("EMAIL_SMTP_HOST", "smtp.qq.com")
EMAIL_SMTP_PORT = int(os.environ.get("EMAIL_SMTP_PORT", "465"))
EMAIL_SMTP_USER = os.environ.get("EMAIL_SMTP_USER", "")
EMAIL_SMTP_PASSWORD = os.environ.get("EMAIL_SMTP_PASSWORD", "")  # QQ邮箱使用授权码
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
EMAIL_TO = os.environ.get("EMAIL_TO", "")  # 接收投资建议的邮箱，多个用逗号分隔

# 短信配置（当 NOTIFY_CHANNELS 包含 sms 时生效）
# 使用阿里云短信服务
SMS_ACCESS_KEY_ID = os.environ.get("SMS_ACCESS_KEY_ID", "")
SMS_ACCESS_KEY_SECRET = os.environ.get("SMS_ACCESS_KEY_SECRET", "")
SMS_SIGN_NAME = os.environ.get("SMS_SIGN_NAME", "")  # 短信签名
SMS_TEMPLATE_CODE = os.environ.get("SMS_TEMPLATE_CODE", "")  # 短信模板ID
SMS_PHONE_NUMBERS = os.environ.get(
    "SMS_PHONE_NUMBERS", ""
)  # 接收短信的手机号，多个用逗号分隔
