# 投资助手后端 (FastAPI版)

本项目是投资助手的后端API，使用FastAPI框架开发。

## 从Django迁移到FastAPI

本项目原本使用Django框架开发，现已迁移到FastAPI，保持接口逻辑和参数完全不变。主要的迁移内容如下：

1. 路由结构：将Django的视图函数转换为FastAPI的路由函数
2. 请求参数：使用路径参数和查询参数替代Django的request.GET
3. 响应格式：使用Python字典直接返回，FastAPI会自动转换为JSON
4. 异常处理：使用HTTPException替代JsonResponse返回错误
5. 异步支持：直接使用异步函数，无需async_to_sync

### Django遗留文件处理

在迁移过程中，以下Django特有的文件已不再需要，可以删除：

- `manage.py` - Django的管理脚本，由FastAPI的run.py替代
- `settings.py` - Django的配置文件，由src/config.py替代
- `urls.py` - Django的URL配置，由FastAPI的路由装饰器替代

Django的数据库模型和缓存系统也已替换：

- Django ORM -> 可以选择SQLAlchemy或其他ORM
- Django Cache -> 自定义的Redis缓存实现
- Django事务装饰器 -> 自定义的事务处理装饰器

## 项目结构

```
backend/
├── requirements.txt      # 依赖项
├── run.py                # 启动脚本
├── src/
│   ├── config.py         # 配置文件
│   ├── main.py           # FastAPI主应用
│   ├── api/
│   │   ├── controller/   # 控制器(路由)
│   │   └── model/        # 模型
│   ├── service/          # 服务层
│   └── infrastructure/   # 基础设施层
│       ├── cache/        # 缓存实现
│       └── db/           # 数据库操作
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动应用

```bash
python run.py
```

应用将在 http://localhost:8000 启动，API文档可以在 http://localhost:8000/docs 访问。

## API接口

所有API接口保持与Django版本一致，包括：

### 黄金接口
- GET /gold/index - 获取黄金指数

### 市场指数接口
- GET /market/{market}/{index_code} - 获取指定市场的指数数据

### 股票接口
- GET /stock/{market}/{index_code} - 获取指定市场的股票指数数据
- GET /stock/quotes/{market} - 获取股票行情数据 