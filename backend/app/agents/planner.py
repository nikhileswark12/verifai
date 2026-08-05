from typing import Any, Dict, List

from app.models import (
    AgentLog,
    AgentName,
    AgentStatus,
    ErrorDetail,
    ResearchState,
    SubClaim,
)
from app.services.anthropic_client import AnthropicClient
from app.services.prompt_loader import load_prompt
import time
from app.core.logging import get_logger
from app.core.metrics import record_agent_start, record_agent_completion

logger = get_logger(__name__)


def _validate_response(response: Dict[str, Any]) -> List[Dict[str, str]]:
    if "sub_claims" not in response:
        raise ValueError("Missing 'sub_claims' key in response.")

    sub_claims = response["sub_claims"]
    if not isinstance(sub_claims, list):
        raise ValueError("'sub_claims' must be a list.")

    if not (3 <= len(sub_claims) <= 8):
        raise ValueError("Must have between 3 and 8 sub_claims.")

    seen_texts = set()
    validated = []

    for item in sub_claims:
        if not isinstance(item, dict):
            raise ValueError("Each sub-claim must be a dictionary.")

        if "text" not in item or "rationale" not in item:
            raise ValueError("Each sub-claim must contain 'text' and 'rationale'.")

        text = item["text"]
        rationale = item["rationale"]

        if not isinstance(text, str) or not text.strip():
            raise ValueError("Sub-claim 'text' cannot be empty.")

        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError("Sub-claim 'rationale' cannot be empty.")

        normalized_text = " ".join(text.strip().casefold().split())
        if normalized_text in seen_texts:
            raise ValueError(f"Duplicate sub-claim detected: {text}")

        seen_texts.add(normalized_text)
        validated.append({"text": text.strip(), "rationale": rationale.strip()})

    return validated


def _create_subclaims(validated_data: List[Dict[str, str]]) -> List[SubClaim]:
    return [
        SubClaim(text=item["text"], rationale=item["rationale"])
        for item in validated_data
    ]


async def _run_planner(state: ResearchState) -> ResearchState:
    if state.error is not None:
        return state

    old_status = state.agent_status[AgentName.PLANNER].upper()
    state.agent_status[AgentName.PLANNER] = AgentStatus.RUNNING
    state.logs.append(AgentLog(agent=AgentName.PLANNER, message=f"{old_status} -> RUNNING"))

    agent_name = "planner"
    start_time = time.time()
    record_agent_start(state, agent_name)
    logger.info("agent_started", extra={"agent": agent_name, "job_id": state.job_id})

    try:
        system_prompt = load_prompt("planner")
        client = AnthropicClient()

        response_json = await client.generate_json(
            system_prompt=system_prompt,
            user_prompt=state.query,
        )

        validated_data = _validate_response(response_json)
        state.sub_claims = _create_subclaims(validated_data)

        state.agent_status[AgentName.PLANNER] = AgentStatus.DONE
        state.logs.append(AgentLog(agent=AgentName.PLANNER, message="RUNNING -> DONE"))
        state.logs.append(
            AgentLog(
                agent=AgentName.PLANNER,
                message="Planner completed successfully.",
            )
        )
        
        duration = time.time() - start_time
        record_agent_completion(state, agent_name, duration)
        logger.info("agent_completed", extra={"agent": agent_name, "job_id": state.job_id, "duration": duration})

    except Exception as e:
        state.agent_status[AgentName.PLANNER] = AgentStatus.ERROR
        state.logs.append(AgentLog(agent=AgentName.PLANNER, message="RUNNING -> ERROR"))
        state.error = ErrorDetail(
            stage=AgentName.PLANNER,
            message=str(e),
            recoverable=False,
            retry_count=0,
        )
        state.logs.append(
            AgentLog(
                agent=AgentName.PLANNER,
                message=f"Planner failed: {e}",
            )
        )
        
        duration = time.time() - start_time
        logger.error("agent_failed", extra={"agent": agent_name, "job_id": state.job_id, "duration": duration, "error": str(e)})

    return state


async def run(state: ResearchState) -> ResearchState:
    return await _run_planner(state)
