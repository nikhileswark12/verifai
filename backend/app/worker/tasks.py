import asyncio
import logging
from app.worker.celery_app import celery_app
from app.services.job_store import JobStore
from app.services.exceptions import JobOwnershipLostError
from app.core.execution_manager import execute_workflow
from app.db.session import async_session
from app.models import AgentName, AgentStatus, ErrorDetail
from app.config import settings
from billiard.exceptions import SoftTimeLimitExceeded

logger = logging.getLogger(__name__)

async def _run_workflow_async(job_id: str, worker_id: str) -> None:
    if not async_session:
        logger.error("async_session is not initialized (DATABASE_URL missing?)")
        return

    async with async_session() as session:
        job_store = JobStore(session)
        
        try:
            # Atomic ownership claim
            claimed = await job_store.claim_job(job_id, worker_id)
            if not claimed:
                logger.warning(f"Job {job_id} is already claimed, completed, or missing. Skipping duplicate execution.")
                return
                
            state = await job_store.get(job_id)
            if not state:
                logger.warning(f"Job {job_id} not found in database after claiming. Skipping.")
                return
                
            # Start heartbeat loop
            async def heartbeat_loop():
                try:
                    while True:
                        await asyncio.sleep(settings.JOB_HEARTBEAT_INTERVAL)
                        try:
                            await job_store.record_heartbeat(job_id, worker_id)
                        except JobOwnershipLostError:
                            logger.error(f"Worker {worker_id} lost ownership during heartbeat for {job_id}")
                            break # cleanly exit heartbeat loop
                        except Exception as e:
                            logger.error(f"Failed to record heartbeat for {job_id}: {e}")
                except asyncio.CancelledError:
                    pass

            hb_task = asyncio.create_task(heartbeat_loop())
            
            try:
                # Execute workflow
                state = await execute_workflow(state, job_store, worker_id=worker_id)
                await job_store.update(state, worker_id=worker_id)
            finally:
                hb_task.cancel()
                try:
                    await hb_task
                except asyncio.CancelledError:
                    pass
            
        except JobOwnershipLostError as e:
            logger.error(f"Ownership lost for job {job_id}. Halting execution: {e}")
            # Do NOT attempt to persist terminal state because we don't own the job
            return
            
        except SoftTimeLimitExceeded as e:
            logger.error(f"Job {job_id} exceeded soft time limit.")
            try:
                state = await job_store.get(job_id)
                if state:
                    state.error = ErrorDetail(
                        stage=AgentName.ORCHESTRATOR,
                        message="Workflow execution timed out.",
                        recoverable=False,
                        retry_count=0
                    )
                    state.agent_status[AgentName.ORCHESTRATOR] = AgentStatus.ERROR
                    await job_store.update(state, worker_id=worker_id)
            except JobOwnershipLostError:
                pass # Lost ownership, do not mutate state
            except Exception as inner_e:
                logger.error(f"Failed to persist timeout state for {job_id}: {inner_e}")
                
        except Exception as e:
            logger.exception(f"Critical failure executing job {job_id}")
            # Try to persist the failure if possible (might fail if the DB connection is broken)
            try:
                state = await job_store.get(job_id)
                if state:
                    state.error = ErrorDetail(
                        stage=AgentName.ORCHESTRATOR,
                        message=f"Worker exception: {str(e)}",
                        recoverable=False,
                        retry_count=0
                    )
                    state.agent_status[AgentName.ORCHESTRATOR] = AgentStatus.ERROR
                    await job_store.update(state, worker_id=worker_id)
            except JobOwnershipLostError:
                pass # Lost ownership, do not mutate state
            except Exception as inner_e:
                logger.error(f"Failed to persist crash state for {job_id}: {inner_e}")


@celery_app.task(
    name="execute_research_job",
    bind=True,
    soft_time_limit=settings.WORKFLOW_SOFT_TIME_LIMIT,
    time_limit=settings.WORKFLOW_HARD_TIME_LIMIT
)
def execute_research_job(self, job_id: str):
    worker_id = self.request.id
    logger.info(f"Starting Celery task {worker_id} for job {job_id}")
    asyncio.run(_run_workflow_async(job_id, worker_id))
    logger.info(f"Finished Celery task for job {job_id}")

@celery_app.task(
    name="sweep_stale_jobs",
    soft_time_limit=10,
    time_limit=15
)
def sweep_stale_jobs():
    logger.info("Stale job sweep started")
    
    async def _sweep():
        if not async_session:
            logger.error("async_session is not initialized (DATABASE_URL missing?)")
            return 0
            
        async with async_session() as session:
            job_store = JobStore(session)
            try:
                recovered = await job_store.recover_stale_jobs(settings.JOB_STALE_TIMEOUT)
                return len(recovered)
            except Exception as e:
                logger.error(f"Failed to recover stale jobs: {e}")
                return 0

    recovered_count = asyncio.run(_sweep())
    
    if recovered_count > 0:
        logger.info(f"Recovered {recovered_count} stale jobs")
        
    logger.info("Stale job sweep completed")
    return {"recovered": recovered_count}
