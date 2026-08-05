import asyncio
from typing import Any, Dict, List

from app.models import (
    AgentLog,
    AgentName,
    AgentStatus,
    Claim,
    ErrorDetail,
    ResearchReport,
    ResearchState,
)
from app.services.anthropic_client import AnthropicClient
from app.services.prompt_loader import load_prompt


from app.core.report_formatter import build_claim_summary, build_contradiction_summary
import json
import time
from app.core.logging import get_logger
from app.core.metrics import record_agent_start, record_agent_completion

logger = get_logger(__name__)

def _collect_report_data(state: ResearchState) -> str:
    prompt = f"Query: {state.query}\n\n"
    prompt += "Verified Claims:\n"
    for claim in state.sub_claims:
        v_res = next(
            (v for v in state.verification_results if v.claim_id == claim.id), None
        )
        claim_summary_dict = build_claim_summary(claim, v_res)
        claim_summary_dict['id'] = claim.id
        prompt += json.dumps(claim_summary_dict, indent=2) + "\n\n"

    if state.contradictions:
        prompt += "Detected Contradictions:\n"
        c_summary = build_contradiction_summary(state.contradictions)
        prompt += json.dumps(c_summary, indent=2) + "\n"
    else:
        prompt += "Detected Contradictions: None\n"

    return prompt


def _collect_references(state: ResearchState) -> List[str]:
    urls = set()
    for ev_list in state.evidence_by_claim.values():
        for ev in ev_list:
            urls.add(str(ev.source.url))
    return sorted(list(urls))


def _validate_response(response: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(response, dict):
        raise ValueError("Response must be a dictionary.")

    required_keys = [
        "executive_summary",
        "overall_assessment",
        "conclusion",
        "contradiction_summary",
        "claim_summaries",
        "references",
    ]
    for key in required_keys:
        if key not in response:
            raise ValueError(f"Missing required key: {key}")

    if not isinstance(response["references"], list):
        raise ValueError("'references' must be a list.")

    unique_refs = set()
    for r in response["references"]:
        if not isinstance(r, str) or not r.startswith("http"):
            raise ValueError("Reference must be a valid URL string.")
        if r in unique_refs:
            raise ValueError("References must be unique.")
        unique_refs.add(r)

    if not isinstance(response["claim_summaries"], list):
        raise ValueError("'claim_summaries' must be a list.")
        
    for c in response["claim_summaries"]:
        if "claim_id" not in c or "summary" not in c or "importance" not in c:
            raise ValueError("Claim summary missing required fields")

    return response


def _build_report(state: ResearchState, validated_data: Dict[str, Any]) -> ResearchReport:
    claims = []

    overall_confidence = 0.0
    if state.verification_results:
        total = sum(v.confidence.overall_score for v in state.verification_results)
        overall_confidence = total / len(state.verification_results)

    for sub_claim in state.sub_claims:
        v_res = next(
            (v for v in state.verification_results if v.claim_id == sub_claim.id), None
        )

        if v_res:
            c_notes = [
                c.explanation for c in state.contradictions if sub_claim.id in c.claim_id
            ]
            
            c_summary_dict = build_claim_summary(sub_claim, v_res)
            
            claim_obj = Claim(
                sub_claim_id=sub_claim.id,
                text=sub_claim.text,
                status=v_res.status,
                evidence=v_res.supporting_evidence + v_res.conflicting_evidence,
                confidence=v_res.confidence,
                contradiction_notes=c_notes,
                supporting_evidence_count=c_summary_dict["supporting_sources"],
                conflicting_evidence_count=c_summary_dict["conflicting_sources"],
                explanation=c_summary_dict["explanation"]
            )
            claims.append(claim_obj)

    unique_refs = _collect_references(state)

    conclusion = validated_data["conclusion"]
    if validated_data.get("contradiction_summary"):
        conclusion += f"\n\nContradictions:\n{validated_data['contradiction_summary']}"

    if unique_refs:
        conclusion += "\n\nReferences:\n" + "\n".join(f"- {ref}" for ref in unique_refs)

    return ResearchReport(
        query=state.query,
        executive_summary=validated_data["executive_summary"],
        claims=claims,
        overall_confidence=overall_confidence,
        conclusion=conclusion,
    )


async def _generate_report(state: ResearchState) -> ResearchState:
    old_status = state.agent_status[AgentName.REPORT].upper()
    state.agent_status[AgentName.REPORT] = AgentStatus.RUNNING
    state.logs.append(AgentLog(agent=AgentName.REPORT, message=f"{old_status} -> RUNNING"))

    agent_name = "report"
    start_time = time.time()
    record_agent_start(state, agent_name)
    logger.info("agent_started", extra={"agent": agent_name, "job_id": state.job_id})

    try:
        client = AnthropicClient()
        system_prompt = load_prompt("reporter")

        user_prompt = _collect_report_data(state)
        response_json = await client.generate_json(
            system_prompt=system_prompt, user_prompt=user_prompt
        )

        validated = _validate_response(response_json)
        report = _build_report(state, validated)

        state.report = report
        state.agent_status[AgentName.REPORT] = AgentStatus.DONE
        state.logs.append(AgentLog(agent=AgentName.REPORT, message="RUNNING -> DONE"))
        state.logs.append(
            AgentLog(
                agent=AgentName.REPORT,
                message="Report generated successfully.",
            )
        )
        
        duration = time.time() - start_time
        record_agent_completion(state, agent_name, duration)
        logger.info("agent_completed", extra={"agent": agent_name, "job_id": state.job_id, "duration": duration})

    except Exception as e:
        state.agent_status[AgentName.REPORT] = AgentStatus.ERROR
        state.logs.append(AgentLog(agent=AgentName.REPORT, message="RUNNING -> ERROR"))
        state.error = ErrorDetail(
            stage=AgentName.REPORT,
            message=str(e),
            recoverable=False,
            retry_count=0,
        )
        state.logs.append(
            AgentLog(
                agent=AgentName.REPORT,
                message=f"Report fatal failure: {e}",
            )
        )
        
        duration = time.time() - start_time
        logger.error("agent_failed", extra={"agent": agent_name, "job_id": state.job_id, "duration": duration, "error": str(e)})
        raise

    return state


async def run(state: ResearchState) -> ResearchState:
    return await _generate_report(state)
