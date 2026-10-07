import pytest
import pytest_asyncio
import uuid
import os
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from app.db.base import Base
from app.models import ResearchState, AgentName, AgentStatus
from app.services.job_store import JobStore

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/verifai_v2_test"

@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(engine):
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
async def job_store(db_session):
    return JobStore(db_session)

@pytest.mark.asyncio
async def test_create_and_retrieve_job(job_store):
    state = ResearchState(query="Test query for persistence")
    await job_store.create(state)
    
    retrieved = await job_store.get(state.job_id)
    assert retrieved is not None
    assert retrieved.job_id == state.job_id
    assert retrieved.query == "Test query for persistence"
    assert retrieved.agent_status[AgentName.PLANNER] == AgentStatus.PENDING

@pytest.mark.asyncio
async def test_nonexistent_job(job_store):
    retrieved = await job_store.get(str(uuid.uuid4()))
    assert retrieved is None

@pytest.mark.asyncio
async def test_update_job_status(job_store):
    state = ResearchState(query="Status update test")
    await job_store.create(state)
    
    state.agent_status[AgentName.ORCHESTRATOR] = AgentStatus.RUNNING
    state.agent_status[AgentName.PLANNER] = AgentStatus.DONE
    await job_store.update(state)
    
    retrieved = await job_store.get(state.job_id)
    assert retrieved.agent_status[AgentName.PLANNER] == AgentStatus.DONE
    assert retrieved.agent_status[AgentName.PLANNER] == AgentStatus.DONE

@pytest.mark.asyncio
async def test_persistence_fresh_instance(db_session):
    store1 = JobStore(db_session)
    state = ResearchState(query="Fresh instance test")
    await store1.create(state)
    
    store2 = JobStore(db_session)
    retrieved = await store2.get(state.job_id)
    assert retrieved.job_id == state.job_id

