import asyncio
import itertools
from typing import Any, Dict, List, Tuple
import json
from pydantic import ValidationError

from app.models import (
    AgentLog,
    AgentName,
    AgentStatus,
    ContradictionPair,
    ErrorDetail,
    Evidence,
    ResearchState,
    Source,
    SourceTier,
    VerificationResult,
)
from app.services.anthropic_client import AnthropicClient
from app.services.prompt_loader import load_prompt
import time
from app.core.logging import get_logger
from app.core.metrics import record_agent_start, record_agent_completion

logger = get_logger(__name__)


def _generate_pairs(
    results: List[VerificationResult],
) -> List[Tuple[VerificationResult, VerificationResult]]:
    return list(itertools.combinations(results, 2))


def _format_pair(res_a: VerificationResult, res_b: VerificationResult) -> str:
    prompt = f"Claim A (ID: {res_a.claim_id}):\n"
    prompt += f"Status: {res_a.status}\n"
    prompt += f"Reasoning: {res_a.reasoning}\n\n"
    prompt += f"Claim B (ID: {res_b.claim_id}):\n"
    prompt += f"Status: {res_b.status}\n"
    prompt += f"Reasoning: {res_b.reasoning}\n"
    return prompt


def _validate_response(response: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(response, dict):
        raise ValueError("Response must be a dictionary.")

    required_keys = ["contradiction", "type", "explanation", "severity"]
    for key in required_keys:
        if key not in response:
            raise ValueError(f"Missing required key: {key}")

    if not isinstance(response["contradiction"], bool):
        raise ValueError("'contradiction' must be a boolean.")

    severity = response["severity"]
    if not (isinstance(severity, (int, float)) and 0.0 <= float(severity) <= 1.0):
        raise ValueError("'severity' must be a float between 0.0 and 1.0.")
        
    valid_types = ["direct", "temporal", "contextual", "partial", "none"]
    if response["type"].lower().strip() not in valid_types:
        raise ValueError(f"Invalid contradiction type: {response['type']}")
        
    return response


def _get_representative_evidence(res: VerificationResult) -> Evidence:
    if res.supporting_evidence:
        return res.supporting_evidence[0]
    if res.conflicting_evidence:
        return res.conflicting_evidence[0]
    
    raise ValueError(f"No evidence available for claim {res.claim_id} to construct contradiction.")


def _build_contradiction(
    res_a: VerificationResult, res_b: VerificationResult, validated_data: Dict[str, Any]
) -> ContradictionPair:
    ev_a = _get_representative_evidence(res_a)
    ev_b = _get_representative_evidence(res_b)

    from app.core.contradiction_classifier import classify_contradiction, calculate_contradiction_severity
    ctype = classify_contradiction(validated_data["type"], ev_a, ev_b)
    cseverity = calculate_contradiction_severity(ctype)

    explanation = validated_data['explanation'].strip()

    return ContradictionPair(
        claim_id=f"{res_a.claim_id},{res_b.claim_id}",
        source_a=ev_a,
        source_b=ev_b,
        explanation=explanation,
        contradiction_type=ctype,
        severity=cseverity
    )


async def _compare_pair(
    res_a: VerificationResult,
    res_b: VerificationResult,
    system_prompt: str,
    client: AnthropicClient,
) -> ContradictionPair | None:
    user_prompt = _format_pair(res_a, res_b)
    response_json = await client.generate_json(
        system_prompt=system_prompt, user_prompt=user_prompt
    )
    validated = _validate_response(response_json)

    if validated["contradiction"] is True:
        return _build_contradiction(res_a, res_b, validated)

    return None


async def _compare_all(state: ResearchState) -> ResearchState:
    old_status = state.agent_status[AgentName.CONTRADICTION].upper()
    state.agent_status[AgentName.CONTRADICTION] = AgentStatus.RUNNING
    state.logs.append(AgentLog(agent=AgentName.CONTRADICTION, message=f"{old_status} -> RUNNING"))

    agent_name = "contradiction"
    start_time = time.time()
    record_agent_start(state, agent_name)
    logger.info("agent_started", extra={"agent": agent_name, "job_id": state.job_id})

    try:
        results = state.verification_results
        pairs = _generate_pairs(results)

        if not pairs:
            state.agent_status[AgentName.CONTRADICTION] = AgentStatus.DONE
            state.logs.append(AgentLog(agent=AgentName.CONTRADICTION, message="RUNNING -> DONE"))
            state.logs.append(
                AgentLog(
                    agent=AgentName.CONTRADICTION,
                    message="Not enough verified claims for contradiction analysis.",
                )
            )
            
            duration = time.time() - start_time
            record_agent_completion(state, agent_name, duration)
            logger.info("agent_completed", extra={"agent": agent_name, "job_id": state.job_id, "duration": duration})
            
            return state

        client = AnthropicClient()
        system_prompt = load_prompt("contradiction")

        tasks = [_compare_pair(a, b, system_prompt, client) for a, b in pairs]
        comparison_results = await asyncio.gather(*tasks, return_exceptions=True)

        for pair, result in zip(pairs, comparison_results):
            if isinstance(result, Exception):
                if isinstance(result, (ValidationError, ValueError, TypeError, json.JSONDecodeError)):
                    raise result
                
                state.logs.append(
                    AgentLog(
                        agent=AgentName.CONTRADICTION,
                        message=f"Comparison failed between {pair[0].claim_id} and {pair[1].claim_id}: {result}",
                    )
                )
            elif result is not None:
                state.contradictions.append(result)

        state.agent_status[AgentName.CONTRADICTION] = AgentStatus.DONE
        state.logs.append(AgentLog(agent=AgentName.CONTRADICTION, message="RUNNING -> DONE"))
        state.logs.append(
            AgentLog(
                agent=AgentName.CONTRADICTION,
                message="Contradiction analysis completed successfully.",
            )
        )
        
        duration = time.time() - start_time
        record_agent_completion(state, agent_name, duration)
        logger.info("agent_completed", extra={"agent": agent_name, "job_id": state.job_id, "duration": duration})

    except Exception as e:
        state.agent_status[AgentName.CONTRADICTION] = AgentStatus.ERROR
        state.logs.append(AgentLog(agent=AgentName.CONTRADICTION, message="RUNNING -> ERROR"))
        state.error = ErrorDetail(
            stage=AgentName.CONTRADICTION,
            message=str(e),
            recoverable=False,
            retry_count=0,
        )
        state.logs.append(
            AgentLog(
                agent=AgentName.CONTRADICTION,
                message=f"Contradiction fatal failure: {e}",
            )
        )
        
        duration = time.time() - start_time
        logger.error("agent_failed", extra={"agent": agent_name, "job_id": state.job_id, "duration": duration, "error": str(e)})
        raise

    return state


async def run(state: ResearchState) -> ResearchState:
    return await _compare_all(state)
