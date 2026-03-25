from sqlalchemy import (
                        Column,
                        Integer,
                        String,
                        DateTime,
                        func,
                        Float,
                        Index,
                        UniqueConstraint
                        )
from src.core.db import Base
from datetime import datetime


class ZoneCount(Base):
    __tablename__ = "zone_counts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_id = Column(String(50), nullable=False)
    cls = Column(String(50), nullable=False)
    count = Column(Integer, default=0)
    snapshot_at = Column(DateTime, server_default=func.now(), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("zone_id", "cls", name="uq_zone_cls"),
    )


class HourlyStats(Base):
    __tablename__ = "hourly_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_id = Column(String(50), nullable=False)
    cls = Column(String(50), nullable=False)
    hour = Column(DateTime, nullable=False)  # truncate to hour
    total = Column(Integer, default=0)
    avg_time = Column(Float, default=0.0)     # avg time_in_zone

