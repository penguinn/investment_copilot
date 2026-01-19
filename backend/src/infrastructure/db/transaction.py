import logging
from functools import wraps
from typing import Any, Callable, TypeVar

# 类型变量
T = TypeVar("T")

logger = logging.getLogger(__name__)


def atomic(func: Callable[..., T]) -> Callable[..., T]:
    """
    数据库事务装饰器，替代Django的transaction.atomic

    在FastAPI中，实际的事务实现将取决于您使用的ORM
    例如SQLAlchemy会使用with session.begin():
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            # TODO: 根据实际使用的ORM替换此处的事务逻辑
            # 例如，使用SQLAlchemy时：
            # async with db.session() as session:
            #     async with session.begin():
            #         return await func(*args, **kwargs, session=session)

            # 临时实现，直接调用函数
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Transaction error: {str(e)}", exc_info=True)
            raise

    return wrapper
