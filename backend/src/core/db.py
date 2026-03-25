# from sqlalchemy import create_engine
# from sqlalchemy.orm import DeclarativeBase
# from sqlalchemy.orm import sessionmaker
#
# from src.core.config import configs
#
#
# engine = create_engine(
#     configs.DATABASE_URL,
#     pool_pre_ping=True,
# )
#
#
# class Base(DeclarativeBase):
#     pass
#
#
# SessionLocal = sessionmaker(bind=engine)
#
#
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
#
#
# def create_tables():
#     Base.metadata.create_all(bind=engine)


from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.core.config import configs
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(
    configs.DATABASE_URL,      # postgresql+asyncpg://user:pass@localhost/dbname
    pool_size=5,
    max_overflow=10,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

if __name__ == '__main__':
    print(configs.DATABASE_URL)