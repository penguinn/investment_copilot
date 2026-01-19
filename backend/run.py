import sys
from pathlib import Path

# 确保 backend 目录在 Python 路径中
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uvicorn
from src.config import API_HOST, API_PORT

if __name__ == "__main__":
    # 启动FastAPI应用（关闭 reload 以便 Ctrl+C 正常工作）
    uvicorn.run(
        "src.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
    )
