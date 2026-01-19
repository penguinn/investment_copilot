"""
通用 Repository 基类
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select, delete, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.database import get_db_session

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Repository 基类"""

    def __init__(self, model: Type[T]):
        self.model = model

    async def create(self, data: Dict[str, Any]) -> T:
        """创建记录"""
        async with get_db_session() as session:
            instance = self.model(**data)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            return instance

    async def create_many(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """批量创建记录"""
        async with get_db_session() as session:
            instances = [self.model(**data) for data in data_list]
            session.add_all(instances)
            await session.flush()
            return instances

    async def get_by_id(self, id: int) -> Optional[T]:
        """根据ID获取记录"""
        async with get_db_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """获取所有记录"""
        async with get_db_session() as session:
            result = await session.execute(
                select(self.model).limit(limit).offset(offset)
            )
            return list(result.scalars().all())

    async def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """更新记录"""
        async with get_db_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == id)
            )
            instance = result.scalar_one_or_none()
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                await session.flush()
                await session.refresh(instance)
            return instance

    async def delete(self, id: int) -> bool:
        """删除记录"""
        async with get_db_session() as session:
            result = await session.execute(
                delete(self.model).where(self.model.id == id)
            )
            return result.rowcount > 0


class TimeSeriesRepository(BaseRepository[T]):
    """时序数据 Repository 基类"""

    def __init__(self, model: Type[T], code_field: str = "code"):
        super().__init__(model)
        self.code_field = code_field
        # 获取模型的所有列名
        self._model_columns = {c.name for c in model.__table__.columns}

    def _filter_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤掉模型中不存在的字段"""
        return {k: v for k, v in data.items() if k in self._model_columns}

    async def save_quote(self, data: Dict[str, Any]) -> T:
        """保存行情数据（upsert）"""
        async with get_db_session() as session:
            filtered_data = self._filter_data(data)
            instance = self.model(**filtered_data)
            await session.merge(instance)
            return instance

    async def save_quotes(self, data_list: List[Dict[str, Any]]) -> int:
        """批量保存行情数据"""
        async with get_db_session() as session:
            for data in data_list:
                filtered_data = self._filter_data(data)
                instance = self.model(**filtered_data)
                await session.merge(instance)
            return len(data_list)

    async def get_latest(self, code: str) -> Optional[T]:
        """获取最新一条记录"""
        async with get_db_session() as session:
            code_column = getattr(self.model, self.code_field)
            result = await session.execute(
                select(self.model)
                .where(code_column == code)
                .order_by(desc(self.model.time))
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def get_latest_all(self, codes: List[str] = None) -> List[T]:
        """获取所有品种的最新记录"""
        async with get_db_session() as session:
            # 使用子查询获取每个code的最新时间
            from sqlalchemy import func
            code_column = getattr(self.model, self.code_field)
            
            subquery = (
                select(
                    code_column,
                    func.max(self.model.time).label("max_time")
                )
                .group_by(code_column)
                .subquery()
            )

            query = select(self.model).join(
                subquery,
                and_(
                    code_column == subquery.c[self.code_field],
                    self.model.time == subquery.c.max_time
                )
            )

            if codes:
                query = query.where(code_column.in_(codes))

            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_history(
        self,
        code: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[T]:
        """获取历史数据"""
        async with get_db_session() as session:
            code_column = getattr(self.model, self.code_field)
            result = await session.execute(
                select(self.model)
                .where(
                    and_(
                        code_column == code,
                        self.model.time >= start_time,
                        self.model.time <= end_time
                    )
                )
                .order_by(self.model.time)
                .limit(limit)
            )
            return list(result.scalars().all())

    async def get_by_time_bucket(
        self,
        code: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "1 hour"
    ) -> List[Dict[str, Any]]:
        """
        获取时间桶聚合数据
        利用 TimescaleDB 的 time_bucket 函数
        """
        from sqlalchemy import text
        async with get_db_session() as session:
            # 使用原生 SQL 利用 TimescaleDB 的 time_bucket
            query = text(f"""
                SELECT 
                    time_bucket('{interval}', time) AS bucket,
                    {self.code_field},
                    FIRST(open, time) as open,
                    MAX(high) as high,
                    MIN(low) as low,
                    LAST(close, time) as close,
                    SUM(volume) as volume
                FROM {self.model.__tablename__}
                WHERE {self.code_field} = :code
                    AND time >= :start_time
                    AND time <= :end_time
                GROUP BY bucket, {self.code_field}
                ORDER BY bucket
            """)
            result = await session.execute(
                query,
                {"code": code, "start_time": start_time, "end_time": end_time}
            )
            return [dict(row._mapping) for row in result.fetchall()]


class WatchlistRepository(BaseRepository[T]):
    """自选列表 Repository 基类"""

    def __init__(self, model: Type[T]):
        super().__init__(model)

    async def get_by_user(self, user_id: str = "default") -> List[T]:
        """获取用户的自选列表"""
        async with get_db_session() as session:
            result = await session.execute(
                select(self.model)
                .where(self.model.user_id == user_id)
                .order_by(self.model.sort_order, self.model.created_at)
            )
            return list(result.scalars().all())

    async def add_to_watchlist(
        self, user_id: str, code: str, name: str = None, **kwargs
    ) -> T:
        """添加到自选"""
        async with get_db_session() as session:
            # 检查是否已存在
            result = await session.execute(
                select(self.model).where(
                    and_(
                        self.model.user_id == user_id,
                        self.model.code == code
                    )
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                return existing

            # 创建新记录
            data = {"user_id": user_id, "code": code, "name": name, **kwargs}
            instance = self.model(**data)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            return instance

    async def remove_from_watchlist(self, user_id: str, code: str) -> bool:
        """从自选中移除"""
        async with get_db_session() as session:
            result = await session.execute(
                delete(self.model).where(
                    and_(
                        self.model.user_id == user_id,
                        self.model.code == code
                    )
                )
            )
            return result.rowcount > 0

    async def update_sort_order(
        self, user_id: str, code: str, sort_order: int
    ) -> bool:
        """更新排序"""
        async with get_db_session() as session:
            result = await session.execute(
                select(self.model).where(
                    and_(
                        self.model.user_id == user_id,
                        self.model.code == code
                    )
                )
            )
            instance = result.scalar_one_or_none()
            if instance:
                instance.sort_order = sort_order
                return True
            return False

    async def is_in_watchlist(self, user_id: str, code: str) -> bool:
        """检查是否在自选中"""
        async with get_db_session() as session:
            result = await session.execute(
                select(self.model).where(
                    and_(
                        self.model.user_id == user_id,
                        self.model.code == code
                    )
                )
            )
            return result.scalar_one_or_none() is not None

    async def get_all_users(self) -> List[str]:
        """获取所有有自选记录的用户ID"""
        async with get_db_session() as session:
            result = await session.execute(
                select(self.model.user_id).distinct()
            )
            users = [row[0] for row in result.fetchall()]
            # 确保至少返回默认用户
            if "default" not in users:
                users.append("default")
            return users
