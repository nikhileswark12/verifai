import time
from datetime import datetime, timezone
import logging

from app.models import ResearchState, AgentName, AgentLog, AgentStatus, ErrorDetail
from app.graph.router import compile_graph
from app.core.retry import should_retry

from app.core.logging import get_logger
logger = get_logger(__name__)

async def execute_workflow(state: ResearchState, job_store=None, worker_id: str = None) -> ResearchState:
    start_time = time.time()
    retry_count = 0
    
    state.metadata["execution"] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "retry_count": retry_count
    }
    
    state.logs.append(
        AgentLog(
            agent=AgentName.ORCHESTRATOR,
            message="Workflow execution started"
        )
    )
    
    logger.info("workflow_started", extra={"job_id": state.job_id, "request_id": state.metadata["execution"].get("request_id")})
    
    graph = compile_graph()
    
    while True:
        try:
            async for output in graph.astream(state):
                for node_name, updated_state in output.items():
                    if isinstance(updated_state, dict):
                        updated_state = ResearchState.model_validate(updated_state)
                    # Update in-place to ensure job_store reference sees updates
                    for key in updated_state.model_fields_set:
                        setattr(state, key, getattr(updated_state, key))
                    
                    if job_store:
                        await job_store.update(state, worker_id=worker_id)
            
            state.metadata["execution"].update({
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": int(time.time() - start_time),
                "status": "completed"
            })
            
            state.logs.append(
                AgentLog(
                    agent=AgentName.ORCHESTRATOR,
                    message="Workflow completed"
                )
            )
            
            logger.info("workflow_completed", extra={"job_id": state.job_id, "duration": state.metadata["execution"]["duration_seconds"]})
            
            return state

        except Exception as e:
            if should_retry(e, retry_count):
                retry_count += 1
                state.metadata["execution"]["retry_count"] = retry_count
                
                state.logs.append(
                    AgentLog(
                        agent=AgentName.ORCHESTRATOR,
                        message=f"Retrying workflow. Attempt {retry_count}"
                    )
                )
                
                # Reset agent statuses to PENDING for retry if they were in ERROR
                for agent_name, status in state.agent_status.items():
                    if status == "error" or status == "running":
                        state.agent_status[agent_name] = "pending"
                
                state.error = None
                continue
                
            else:
                state.metadata["execution"].update({
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "duration_seconds": int(time.time() - start_time),
                    "status": "failed"
                })
                
                if state.error is None:
                    state.error = ErrorDetail(
                        stage=AgentName.ORCHESTRATOR,
                        message=str(e),
                        recoverable=False,
                        retry_count=retry_count
                    )
                
                state.agent_status[state.error.stage] = AgentStatus.ERROR
                
                state.logs.append(
                    AgentLog(
                        agent=AgentName.ORCHESTRATOR,
                        message=f"Workflow failed: {e}"
                    )
                )
                
                logger.error("workflow_failed", extra={"job_id": state.job_id, "error": str(e), "stage": state.error.stage})
                
                return state
