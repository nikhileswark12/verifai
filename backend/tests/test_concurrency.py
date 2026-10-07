import pytest
import pytest_asyncio
import asyncio
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
async def session_maker(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.mark.asyncio
async def test_concurrency_single_worker(session_maker):
    async with session_maker() as session:
        store = JobStore(session)
        state = ResearchState(query="Single worker")
        await store.create(state)
        job_id = state.job_id
        
    async with session_maker() as session:
        store = JobStore(session)
        claimed = await store.claim_job(job_id, "test_worker")
        assert claimed is True
        
        # Verify it is now RUNNING
        retrieved = await store.get(job_id)
        assert retrieved.agent_status[AgentName.ORCHESTRATOR] == AgentStatus.RUNNING

@pytest.mark.asyncio
async def test_concurrency_sequential_duplicate(session_maker):
    async with session_maker() as session:
        store = JobStore(session)
        state = ResearchState(query="Sequential duplicate")
        await store.create(state)
        job_id = state.job_id
        
    async with session_maker() as session:
        store = JobStore(session)
        claimed1 = await store.claim_job(job_id, "test_worker")
        assert claimed1 is True
        
    async with session_maker() as session:
        store = JobStore(session)
        claimed2 = await store.claim_job(job_id, "test_worker")
        assert claimed2 is False

@pytest.mark.asyncio
async def test_concurrency_concurrent_duplicate(session_maker):
    async with session_maker() as session:
        store = JobStore(session)
        state = ResearchState(query="Concurrent duplicate")
        await store.create(state)
        job_id = state.job_id
        
    async def try_claim():
        async with session_maker() as session:
            store = JobStore(session)
            return await store.claim_job(job_id, "test_worker")
            
    results = await asyncio.gather(
        try_claim(),
        try_claim(),
        try_claim(),
        try_claim()
    )
    
    # Exactly one should have claimed it
    claims = [r for r in results if r is True]
    assert len(claims) == 1
    assert results.count(False) == 3

@pytest.mark.asyncio
async def test_concurrency_done_job(session_maker):
    async with session_maker() as session:
        store = JobStore(session)
        state = ResearchState(query="Done job")
        state.agent_status[AgentName.ORCHESTRATOR] = AgentStatus.DONE
        await store.create(state)
        job_id = state.job_id
        
    async with session_maker() as session:
        store = JobStore(session)
        claimed = await store.claim_job(job_id, "test_worker")
        assert claimed is False

@pytest.mark.asyncio
async def test_concurrency_error_job(session_maker):
    async with session_maker() as session:
        store = JobStore(session)
        state = ResearchState(query="Error job")
        state.agent_status[AgentName.ORCHESTRATOR] = AgentStatus.ERROR
        await store.create(state)
        job_id = state.job_id
        
    async with session_maker() as session:
        store = JobStore(session)
        claimed = await store.claim_job(job_id, "test_worker")
        assert claimed is False

