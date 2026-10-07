from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.services.job_store import JobStore

async def get_job_store(session: AsyncSession = Depends(get_db_session)) -> JobStore:
    return JobStore(session)
