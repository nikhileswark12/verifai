import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = None
async_session = None

if DATABASE_URL:
    engine = create_async_engine(DATABASE_URL, echo=False, poolclass=NullPool)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_session():
    if async_session is None:
        raise ValueError("DATABASE_URL is not set in environment.")
    async with async_session() as session:
        yield session
