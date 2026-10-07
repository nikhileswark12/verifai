import pytest
import pytest_asyncio
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from app.models import ResearchState, AgentStatus, AgentName, ErrorDetail
from app.services.job_store import JobStore
from app.services.exceptions import JobOwnershipLostError

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from app.db.base import Base

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

@pytest.fixture
def sample_state():
    return ResearchState(query="Test query")

async def _setup_job(job_store, state):
    await job_store.create(state)
    return state.job_id

@pytest.mark.asyncio
async def test_ownership_correct_worker_can_update(job_store, sample_state):
    job_id = await _setup_job(job_store, sample_state)
    
    # Worker A claims
    worker_a = "worker-A"
    claimed = await job_store.claim_job(job_id, worker_a)
    assert claimed is True
    
    # Worker A updates
    sample_state.agent_status[AgentName.PLANNER] = AgentStatus.DONE
    await job_store.update(sample_state, worker_id=worker_a)
    
    # Verify update succeeded
    state = await job_store.get(job_id)
    assert state.agent_status[AgentName.PLANNER] == AgentStatus.DONE

@pytest.mark.asyncio
async def test_ownership_wrong_worker_cannot_update(job_store, sample_state):
    job_id = await _setup_job(job_store, sample_state)
    
    # Worker A claims
    worker_a = "worker-A"
    await job_store.claim_job(job_id, worker_a)
    
    # Worker B tries to update
    worker_b = "worker-B"
    sample_state.agent_status[AgentName.PLANNER] = AgentStatus.DONE
    
    with pytest.raises(JobOwnershipLostError):
        await job_store.update(sample_state, worker_id=worker_b)
        
    # Verify A's ownership remains and state is unchanged
    state = await job_store.get(job_id)
    assert state.agent_status.get(AgentName.PLANNER) != AgentStatus.DONE

@pytest.mark.asyncio
async def test_ownership_stale_worker_cannot_overwrite_reclaimed_job(db_session, job_store, sample_state):
    job_id = await _setup_job(job_store, sample_state)
    
    # Worker A claims
    worker_a = "worker-A"
    await job_store.claim_job(job_id, worker_a)
    
    # Simulate A becoming stale (move heartbeat_at to past)
    from sqlalchemy import update
    from app.db.models import ResearchJob
    stmt = update(ResearchJob).where(ResearchJob.id == uuid.UUID(job_id)).values(
        heartbeat_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    # Sweeper runs
    recovered = await job_store.recover_stale_jobs(60)
    assert job_id in recovered
    
    # Worker B claims
    worker_b = "worker-B"
    claimed_b = await job_store.claim_job(job_id, worker_b)
    assert claimed_b is True
    
    # Worker A eventually wakes up and tries to update
    sample_state.agent_status[AgentName.PLANNER] = AgentStatus.DONE
    with pytest.raises(JobOwnershipLostError):
        await job_store.update(sample_state, worker_id=worker_a)
        
    # Verify B is unharmed
    state = await job_store.get(job_id)
    assert state.agent_status.get(AgentName.PLANNER) != AgentStatus.DONE

@pytest.mark.asyncio
async def test_ownership_stale_heartbeat_cannot_overwrite_new_worker(db_session, job_store, sample_state):
    job_id = await _setup_job(job_store, sample_state)
    
    worker_a = "worker-A"
    await job_store.claim_job(job_id, worker_a)
    
    from sqlalchemy import update
    from app.db.models import ResearchJob
    stmt = update(ResearchJob).where(ResearchJob.id == uuid.UUID(job_id)).values(
        heartbeat_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    await job_store.recover_stale_jobs(60)
    
    worker_b = "worker-B"
    await job_store.claim_job(job_id, worker_b)
    
    # Worker A tries to heartbeat
    with pytest.raises(JobOwnershipLostError):
        await job_store.record_heartbeat(job_id, worker_a)

@pytest.mark.asyncio
async def test_ownership_current_worker_can_complete_normally(job_store, sample_state):
    job_id = await _setup_job(job_store, sample_state)
    worker_b = "worker-B"
    await job_store.claim_job(job_id, worker_b)
    
    sample_state.agent_status[AgentName.ORCHESTRATOR] = AgentStatus.DONE
    await job_store.update(sample_state, worker_id=worker_b)
    
    state = await job_store.get(job_id)
    assert state.agent_status[AgentName.ORCHESTRATOR] == AgentStatus.DONE
