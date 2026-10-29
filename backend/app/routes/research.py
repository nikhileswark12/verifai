from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
import logging

from app.dependencies import get_job_store
from app.core.execution_manager import execute_workflow
from app.models import (
    AgentName,
    AgentStatus,
    ResearchAcceptedResponse,
    ResearchErrorResponse,
    ResearchReport,
    ResearchRequest,
    ResearchState,
    ResearchStatusResponse,
    ErrorDetail,
)
from app.services.job_store import JobStore
from app.worker.tasks import execute_research_job

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/research", status_code=202, response_model=ResearchAcceptedResponse)
async def create_research_job(
    request: ResearchRequest,
    job_store: JobStore = Depends(get_job_store),
) -> ResearchAcceptedResponse:
    from app.middleware.request_id import request_id_context
    req_id = request_id_context.get()
    
    state = ResearchState(
        query=request.query,
        metadata={
            "execution": {
                "request_id": req_id
            }
        }
    )
    # The default job_id is generated inside ResearchState
    state.metadata["execution"]["job_id"] = state.job_id

    await job_store.create(state)

    try:
        execute_research_job.delay(state.job_id)
    except Exception as exc:
        logger.exception("Unable to enqueue research job %s", state.job_id)
        state.error = ErrorDetail(
            stage=AgentName.ORCHESTRATOR,
            message="The research job could not be queued. Check Redis and Celery configuration.",
            recoverable=True,
            retry_count=0,
        )
        state.agent_status[AgentName.ORCHESTRATOR] = AgentStatus.ERROR
        state.metadata.setdefault("execution", {})["status"] = "failed"
        try:
            await job_store.update(state)
        except Exception:
            logger.exception("Unable to persist queue failure for job %s", state.job_id)
        raise HTTPException(
            status_code=503,
            detail="Research queue is unavailable. Check Redis and retry the request.",
        ) from exc

    return ResearchAcceptedResponse(job_id=state.job_id)


@router.get(
    "/research/{job_id}",
    response_model=ResearchStatusResponse,
    responses={404: {"model": ResearchErrorResponse}},
)
async def get_research_status(
    job_id: str, job_store: JobStore = Depends(get_job_store)
) -> ResearchStatusResponse:
    state = await job_store.get(job_id)
    if not state:
        error_response = ResearchErrorResponse(
            error=True,
            stage=AgentName.ORCHESTRATOR,
            message="Job not found.",
        )
        return JSONResponse(status_code=404, content=error_response.model_dump())

    if state.report is not None:
        overall_status = "completed"
    elif state.error is not None or any(value == AgentStatus.ERROR for value in state.agent_status.values()):
        overall_status = "failed"
    elif any(value == AgentStatus.RUNNING for value in state.agent_status.values()) or any(
        value == AgentStatus.DONE for value in state.agent_status.values()
    ):
        overall_status = "running"
    else:
        overall_status = "pending"

    return ResearchStatusResponse(
        job_id=state.job_id,
        status=overall_status,
        agent_status=state.agent_status,
        error_message=state.error.message if state.error else None,
    )


@router.get(
    "/research/{job_id}/result",
    response_model=ResearchReport,
    responses={
        202: {"description": "Job is still running"},
        404: {"model": ResearchErrorResponse, "description": "Job not found"},
        500: {"model": ResearchErrorResponse, "description": "Job failed"}
    },
)
async def get_research_result(
    job_id: str, job_store: JobStore = Depends(get_job_store)
):
    state = await job_store.get(job_id)
    if not state:
        error_response = ResearchErrorResponse(
            error=True,
            stage=AgentName.ORCHESTRATOR,
            message="Job not found.",
        )
        return JSONResponse(status_code=404, content=error_response.model_dump())

    if state.error:
        error_response = ResearchErrorResponse(
            error=True,
            stage=state.error.stage,
            message=state.error.message,
        )
        return JSONResponse(status_code=500, content=error_response.model_dump())

    if state.report is not None:
        return state.report

    return JSONResponse(status_code=202, content={"status": "running"})
