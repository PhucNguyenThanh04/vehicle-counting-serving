from src.core.database.db import Base
from sqlalchemy import Column, Integer, String, DateTime, func


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, nullable=False)
    cls_name = Column(String(50), nullable=False)
    zone_id = Column(Integer, nullable=False)
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    direction = Column(String(10), nullable=False)  # huong di
    speed = Column(Integer, nullable=False)
    time_in_zone = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())



