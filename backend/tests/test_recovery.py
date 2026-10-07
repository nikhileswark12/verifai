import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import text
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
async def test_recovery_active_running_job(session_maker):
    async with session_maker() as session:
        store = JobStore(session)
        state = ResearchState(query="Active job")
        await store.create(state)
        job_id = state.job_id
        await store.claim_job(job_id, "worker_1")
        
    async with session_maker() as session:
        store = JobStore(session)
        recovered = await store.recover_stale_jobs(120)
        assert len(recovered) == 0

@pytest.mark.asyncio
async def test_recovery_stale_running_job(session_maker):
    async with session_maker() as session:
        store = JobStore(session)
        state = ResearchState(query="Stale job")
        await store.create(state)
        job_id = state.job_id
        await store.claim_job(job_id, "worker_1")
        
        # Manually backdate heartbeat
        await session.execute(text(f"UPDATE research_jobs SET heartbeat_at = NOW() - INTERVAL '150 seconds' WHERE id = '{job_id}'"))
        await session.commit()
        
    async with session_maker() as session:
        store = JobStore(session)
        recovered = await store.recover_stale_jobs(120)
        assert len(recovered) == 1
        assert recovered[0] == job_id
        
        state = await store.get(job_id)
        assert state.agent_status[AgentName.ORCHESTRATOR] == AgentStatus.PENDING

@pytest.mark.asyncio
async def test_recovery_concurrent_sweeps(session_maker):
    async with session_maker() as session:
        store = JobStore(session)
        state = ResearchState(query="Concurrent recovery")
        await store.create(state)
        job_id = state.job_id
        await store.claim_job(job_id, "worker_1")
        
        await session.execute(text(f"UPDATE research_jobs SET heartbeat_at = NOW() - INTERVAL '150 seconds' WHERE id = '{job_id}'"))
        await session.commit()
        
    async def try_recover():
        async with session_maker() as session:
            store = JobStore(session)
            return await store.recover_stale_jobs(120)
            
    results = await asyncio.gather(
        try_recover(), try_recover(), try_recover()
    )
    
    # Flatten the lists
    all_recovered = [jid for sublist in results for jid in sublist]
    assert len(all_recovered) == 1
    assert all_recovered[0] == job_id

@pytest.mark.asyncio
async def test_heartbeat_advances_timestamp(session_maker):
    async with session_maker() as session:
        store = JobStore(session)
        state = ResearchState(query="Heartbeat test")
        await store.create(state)
        job_id = state.job_id
        await store.claim_job(job_id, "worker_1")
        
        # Get current heartbeat
        res = await session.execute(text(f"SELECT heartbeat_at FROM research_jobs WHERE id = '{job_id}'"))
        hb1 = res.scalar_one()
        
    await asyncio.sleep(1.0)
    
    async with session_maker() as session:
        store = JobStore(session)
        await store.record_heartbeat(job_id, "worker_1")
        
        res = await session.execute(text(f"SELECT heartbeat_at FROM research_jobs WHERE id = '{job_id}'"))
        hb2 = res.scalar_one()
        
        assert hb2 > hb1

@pytest.mark.asyncio
async def test_recovery_done_error_ignored(session_maker):
    async with session_maker() as session:
        store = JobStore(session)
        
        state1 = ResearchState(query="Done job")
        await store.create(state1)
        await store.claim_job(state1.job_id, "worker_1")
        await session.execute(text(f"UPDATE research_jobs SET status = 'DONE', heartbeat_at = NOW() - INTERVAL '150 seconds' WHERE id = '{state1.job_id}'"))
        
        state2 = ResearchState(query="Error job")
        await store.create(state2)
        await store.claim_job(state2.job_id, "worker_1")
        await session.execute(text(f"UPDATE research_jobs SET status = 'ERROR', heartbeat_at = NOW() - INTERVAL '150 seconds' WHERE id = '{state2.job_id}'"))
        
        await session.commit()
        
    async with session_maker() as session:
        store = JobStore(session)
        recovered = await store.recover_stale_jobs(120)
        assert len(recovered) == 0

@pytest.mark.asyncio
async def test_timeout_handling(session_maker):
    from app.worker.tasks import _run_workflow_async
    from billiard.exceptions import SoftTimeLimitExceeded
    from unittest.mock import patch
    
    async with session_maker() as session:
        store = JobStore(session)
        state = ResearchState(query="Timeout job")
        await store.create(state)
        job_id = state.job_id
        
    # Mock execute_workflow to raise SoftTimeLimitExceeded
    async def mock_execute(*args, **kwargs):
        raise SoftTimeLimitExceeded("Timeout!")
        
    with patch("app.worker.tasks.async_session", new=session_maker):
        with patch("app.worker.tasks.execute_workflow", new=mock_execute):
            await _run_workflow_async(job_id, "worker_1")
        
    async with session_maker() as session:
        store = JobStore(session)
        state = await store.get(job_id)
        assert state.agent_status[AgentName.ORCHESTRATOR] == AgentStatus.ERROR
        assert state.error is not None
        assert state.error.message == "Workflow execution timed out."

@pytest.mark.asyncio
async def test_sweep_stale_jobs_task(session_maker):
    from app.worker.tasks import sweep_stale_jobs
    from unittest.mock import patch
    
    async with session_maker() as session:
        store = JobStore(session)
        
        # 1 stale job
        state1 = ResearchState(query="Stale job")
        await store.create(state1)
        await store.claim_job(state1.job_id, "worker_1")
        await session.execute(text(f"UPDATE research_jobs SET heartbeat_at = NOW() - INTERVAL '150 seconds' WHERE id = '{state1.job_id}'"))
        
        # 1 healthy job
        state2 = ResearchState(query="Healthy job")
        await store.create(state2)
        await store.claim_job(state2.job_id, "worker_2")
        
        await session.commit()

    # Call the Celery task directly via thread pool to avoid asyncio.run() loop collision
    with patch("app.worker.tasks.async_session", new=session_maker):
        import concurrent.futures
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, sweep_stale_jobs)
        
    assert result == {"recovered": 1}
    
    async with session_maker() as session:
        store = JobStore(session)
        s1 = await store.get(state1.job_id)
        assert s1.agent_status[AgentName.ORCHESTRATOR] == AgentStatus.PENDING
        
        s2 = await store.get(state2.job_id)
        assert s2.agent_status[AgentName.ORCHESTRATOR] == AgentStatus.RUNNING

def test_celery_beat_config_present():
    from app.worker.celery_app import celery_app
    
    beat_schedule = celery_app.conf.beat_schedule
    assert "sweep-stale-jobs-every-60s" in beat_schedule
    
    config = beat_schedule["sweep-stale-jobs-every-60s"]
    assert config["task"] == "sweep_stale_jobs"
    assert config["schedule"] == 60.0
