from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import logging

from app.dependencies import get_job_store
from app.core.execution_manager import execute_workflow
from app.models import (
    AgentName,
    ResearchAcceptedResponse,
    ResearchErrorResponse,
    ResearchReport,
    ResearchRequest,
    ResearchState,
    ResearchStatusResponse,
)
from app.services.job_store import JobStore

router = APIRouter()
logger = logging.getLogger(__name__)


async def _run_workflow_task(job_id: str, job_store: JobStore) -> None:
    state = job_store.get(job_id)
    if not state:
        return

    try:
        state = await execute_workflow(state)
        job_store.update(state)
    except Exception as e:
        logger.error(f"Workflow task failed: {e}")
        job_store.update(state)


@router.post("/research", status_code=202, response_model=ResearchAcceptedResponse)
def create_research_job(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
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

    job_store.create(state)

    background_tasks.add_task(_run_workflow_task, state.job_id, job_store)

    return ResearchAcceptedResponse(job_id=state.job_id)


@router.get(
    "/research/{job_id}",
    response_model=ResearchStatusResponse,
    responses={404: {"model": ResearchErrorResponse}},
)
def get_research_status(
    job_id: str, job_store: JobStore = Depends(get_job_store)
) -> ResearchStatusResponse:
    state = job_store.get(job_id)
    if not state:
        error_response = ResearchErrorResponse(
            error=True,
            stage=AgentName.ORCHESTRATOR,
            message="Job not found.",
        )
        return JSONResponse(status_code=404, content=error_response.model_dump())

    return ResearchStatusResponse(
        job_id=state.job_id,
        agent_status=state.agent_status,
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
def get_research_result(
    job_id: str, job_store: JobStore = Depends(get_job_store)
):
    state = job_store.get(job_id)
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
