from src.core.database.db import Base
from sqlalchemy import Column, String, Boolean, DateTime, func
import uuid
from sqlalchemy.dialects.postgresql import UUID


class Auth(Base):
    __tablename__ = "auth"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4()
    )
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    fullname = Column(String(200), nullable=False)
    phone = Column(String(15), unique=True)
    password_hash = Column(String(255), nullable=False)
    refresh_token_hash = Column(String(255))

    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)


