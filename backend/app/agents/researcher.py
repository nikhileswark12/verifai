import asyncio
from typing import Any, Dict, List
from urllib.parse import urlparse
import json
from pydantic import ValidationError

from app.models import (
    AgentLog,
    AgentName,
    AgentStatus,
    ErrorDetail,
    Evidence,
    ResearchState,
    Source,
    SourceTier,
    SubClaim,
)
from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider, SearchResult
from app.core.query_expander import expand_query
from app.core.source_ranker import rank_source
from app.core.evidence_matcher import deduplicate_evidence
import time
from app.core.logging import get_logger
from app.core.metrics import record_agent_start, record_agent_completion

logger = get_logger(__name__)


def _create_source(result: SearchResult) -> Source:
    url_str = result.url.strip()
    parsed_url = urlparse(url_str)
    domain = parsed_url.netloc or ""
    
    tier = rank_source(url_str)

    return Source(
        name=result.title.strip(),
        domain=domain,
        url=url_str,
        tier=tier,
    )


def _create_evidence(source: Source, snippet: str) -> Evidence:
    return Evidence(
        source=source,
        snippet=snippet,
    )


class Researcher:
    def __init__(self, llm: LLMProvider, search: SearchProvider):
        self.llm = llm
        self.search = search

    async def _search_claim(self, claim: SubClaim) -> List[Evidence]:
        queries = await expand_query(claim.text, self.llm)
        
        try:
            results = await self.search.search_multiple(queries=queries, max_results=5)
        except Exception:
            results = []

        evidence_list = []
        for result in results:
            source = _create_source(result)
            snippet = result.content.strip()

            if len(snippet) > 1000:
                snippet = snippet[:997] + "..."

            evidence = _create_evidence(source, snippet)
            evidence_list.append(evidence)

        unique_evidence = deduplicate_evidence(evidence_list)
        return unique_evidence

    async def _collect_evidence(self, state: ResearchState) -> ResearchState:
        old_status = state.agent_status[AgentName.RESEARCH].upper()
        state.agent_status[AgentName.RESEARCH] = AgentStatus.RUNNING
        state.logs.append(AgentLog(agent=AgentName.RESEARCH, message=f"{old_status} -> RUNNING"))

        agent_name = "research"
        start_time = time.time()
        record_agent_start(state, agent_name)
        logger.info("agent_started", extra={"agent": agent_name, "job_id": state.job_id})

        try:
            claims = state.sub_claims

            if not claims:
                state.agent_status[AgentName.RESEARCH] = AgentStatus.DONE
                state.logs.append(AgentLog(agent=AgentName.RESEARCH, message="RUNNING -> DONE"))
                state.logs.append(
                    AgentLog(
                        agent=AgentName.RESEARCH,
                        message="No sub-claims to research.",
                    )
                )
                
                duration = time.time() - start_time
                record_agent_completion(state, agent_name, duration)
                logger.info("agent_completed", extra={"agent": agent_name, "job_id": state.job_id, "duration": duration})
                
                return state

            tasks = [self._search_claim(claim) for claim in claims]
            results_by_claim = await asyncio.gather(*tasks, return_exceptions=True)

            for claim, results in zip(claims, results_by_claim):
                if isinstance(results, Exception):
                    from app.services.exceptions import JSONParseError
                    if isinstance(results, (ValidationError, ValueError, TypeError, json.JSONDecodeError, JSONParseError)):
                        raise results
                    
                    state.logs.append(
                        AgentLog(
                            agent=AgentName.RESEARCH,
                            message=f"Search failed for claim '{claim.id}': {results}",
                        )
                    )
                    state.evidence_by_claim[claim.id] = []
                else:
                    state.evidence_by_claim[claim.id] = results

            state.agent_status[AgentName.RESEARCH] = AgentStatus.DONE
            state.logs.append(AgentLog(agent=AgentName.RESEARCH, message="RUNNING -> DONE"))
            state.logs.append(
                AgentLog(
                    agent=AgentName.RESEARCH,
                    message="Research completed successfully.",
                )
            )
            
            duration = time.time() - start_time
            record_agent_completion(state, agent_name, duration)
            logger.info("agent_completed", extra={"agent": agent_name, "job_id": state.job_id, "duration": duration})

        except Exception as e:
            state.agent_status[AgentName.RESEARCH] = AgentStatus.ERROR
            state.logs.append(AgentLog(agent=AgentName.RESEARCH, message="RUNNING -> ERROR"))
            state.error = ErrorDetail(
                stage=AgentName.RESEARCH,
                message=str(e),
                recoverable=False,
                retry_count=0,
            )
            state.logs.append(
                AgentLog(
                    agent=AgentName.RESEARCH,
                    message=f"Research fatal failure: {e}",
                )
            )
            
            duration = time.time() - start_time
            logger.error("agent_failed", extra={"agent": agent_name, "job_id": state.job_id, "duration": duration, "error": str(e)})
            raise

        return state

    async def run(self, state: ResearchState) -> ResearchState:
        return await self._collect_evidence(state)
