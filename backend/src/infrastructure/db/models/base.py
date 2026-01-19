from datetime import datetime

from sqlalchemy import Column, DateTime, Index, String
from sqlalchemy.ext.declarative import declared_attr

from src.infrastructure.db.database import Base


class TimeSeriesBase:
    """时序数据基类 Mixin"""

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    time = Column(DateTime, primary_key=True, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    @declared_attr
    def __table_args__(cls):
        return (
            Index(f"ix_{cls.__tablename__}_time", "time", postgresql_using="btree"),
        )
