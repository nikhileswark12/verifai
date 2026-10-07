import asyncio
from typing import Any, Dict, List
import json
from pydantic import ValidationError

from app.models import (
    AgentLog,
    AgentName,
    AgentStatus,
    ClaimStatus,
    ConfidenceBreakdown,
    ErrorDetail,
    Evidence,
    ResearchState,
    SubClaim,
    VerificationResult,
)
from app.providers.llm.base import LLMProvider
from app.services.prompt_loader import load_prompt
import time
from app.core.logging import get_logger
from app.core.metrics import record_agent_start, record_agent_completion

logger = get_logger(__name__)


def _format_evidence(claim: SubClaim, evidence_list: List[Evidence]) -> str:
    prompt = f"Claim to verify: {claim.text}\nRationale: {claim.rationale}\n\nEvidence:\n"
    if not evidence_list:
        prompt += "No evidence available."
    else:
        for i, ev in enumerate(evidence_list, 1):
            prompt += f"[{i}] ID: {ev.id}\nSource: {ev.source.name} ({ev.source.domain})\n"
            prompt += f"Snippet: {ev.snippet}\n\n"
    return prompt


def _validate_response(response: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(response, dict):
        raise ValueError("Response must be a dictionary.")

    required_keys = ["status", "summary", "reasoning", "supporting_evidence_ids", "conflicting_evidence_ids"]
    for key in required_keys:
        if key not in response:
            raise ValueError(f"Missing required key: {key}")

    status_str = response["status"]
    if not hasattr(ClaimStatus, status_str):
        raise ValueError(f"Invalid status: {status_str}")

    supp = response["supporting_evidence_ids"]
    conf = response["conflicting_evidence_ids"]
    if not isinstance(supp, list) or not isinstance(conf, list):
        raise ValueError("Evidence IDs must be lists.")

    return response


def _build_verification(
    claim_id: str, evidence_list: List[Evidence], validated_data: Dict[str, Any]
) -> VerificationResult:

    status = ClaimStatus[validated_data["status"]]
    
    ev_dict = {ev.id: ev for ev in evidence_list}
    
    supporting = []
    for eid in validated_data["supporting_evidence_ids"]:
        if eid not in ev_dict:
            raise ValueError(f"Unknown supporting evidence ID: {eid}")
        supporting.append(ev_dict[eid])
        
    conflicting = []
    for eid in validated_data["conflicting_evidence_ids"]:
        if eid not in ev_dict:
            raise ValueError(f"Unknown conflicting evidence ID: {eid}")
        conflicting.append(ev_dict[eid])
        
    from app.core.confidence import calculate_confidence
    confidence = calculate_confidence(supporting, conflicting)

    reasoning = f"{validated_data['summary']}\n\n{validated_data['reasoning']}".strip()

    return VerificationResult(
        claim_id=claim_id,
        status=status,
        supporting_evidence=supporting,
        conflicting_evidence=conflicting,
        confidence=confidence,
        reasoning=reasoning,
    )


class Verifier:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def _verify_claim(
        self,
        claim: SubClaim,
        evidence_list: List[Evidence],
        system_prompt: str,
    ) -> VerificationResult:
        user_prompt = _format_evidence(claim, evidence_list)
        response_json = await self.llm.generate_json(
            system_prompt=system_prompt, user_prompt=user_prompt
        )
        validated = _validate_response(response_json)
        return _build_verification(claim.id, evidence_list, validated)

    async def _verify_all(self, state: ResearchState) -> ResearchState:
        old_status = state.agent_status[AgentName.VERIFICATION].upper()
        state.agent_status[AgentName.VERIFICATION] = AgentStatus.RUNNING
        state.logs.append(AgentLog(agent=AgentName.VERIFICATION, message=f"{old_status} -> RUNNING"))

        agent_name = "verification"
        start_time = time.time()
        record_agent_start(state, agent_name)
        logger.info("agent_started", extra={"agent": agent_name, "job_id": state.job_id})

        try:
            system_prompt = load_prompt("verifier")

            claims = state.sub_claims
            if not claims:
                state.agent_status[AgentName.VERIFICATION] = AgentStatus.DONE
                state.logs.append(AgentLog(agent=AgentName.VERIFICATION, message="RUNNING -> DONE"))
                state.logs.append(
                    AgentLog(
                        agent=AgentName.VERIFICATION, message="No claims to verify."
                    )
                )
                
                duration = time.time() - start_time
                record_agent_completion(state, agent_name, duration)
                logger.info("agent_completed", extra={"agent": agent_name, "job_id": state.job_id, "duration": duration})
                
                return state

            tasks = []
            for claim in claims:
                evidence_list = state.evidence_by_claim.get(claim.id, [])
                tasks.append(self._verify_claim(claim, evidence_list, system_prompt))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for claim, result in zip(claims, results):
                if isinstance(result, Exception):
                    if isinstance(result, (ValidationError, ValueError, TypeError, json.JSONDecodeError)):
                        raise result
                    
                    state.logs.append(
                        AgentLog(
                            agent=AgentName.VERIFICATION,
                            message=f"Verification failed for claim '{claim.id}': {result}",
                        )
                    )
                else:
                    state.verification_results.append(result)

            state.agent_status[AgentName.VERIFICATION] = AgentStatus.DONE
            state.logs.append(AgentLog(agent=AgentName.VERIFICATION, message="RUNNING -> DONE"))
            state.logs.append(
                AgentLog(
                    agent=AgentName.VERIFICATION,
                    message="Verification completed successfully.",
                )
            )
            
            duration = time.time() - start_time
            record_agent_completion(state, agent_name, duration)
            logger.info("agent_completed", extra={"agent": agent_name, "job_id": state.job_id, "duration": duration})

        except Exception as e:
            state.agent_status[AgentName.VERIFICATION] = AgentStatus.ERROR
            state.logs.append(AgentLog(agent=AgentName.VERIFICATION, message="RUNNING -> ERROR"))
            state.error = ErrorDetail(
                stage=AgentName.VERIFICATION,
                message=str(e),
                recoverable=False,
                retry_count=0,
            )
            state.logs.append(
                AgentLog(
                    agent=AgentName.VERIFICATION,
                    message=f"Verification fatal failure: {e}",
                )
            )
            
            duration = time.time() - start_time
            logger.error("agent_failed", extra={"agent": agent_name, "job_id": state.job_id, "duration": duration, "error": str(e)})
            raise

        return state

    async def run(self, state: ResearchState) -> ResearchState:
        return await self._verify_all(state)
