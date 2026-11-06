import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

os.environ["OPENROUTER_API_KEY"] = "mocked-openrouter-key"
os.environ["TAVILY_API_KEY"] = "mocked-tavily-key"

from app.agents.verifier import Verifier
from app.graph.workflow import _route_after_agent
from app.models import AgentName, AgentStatus, ErrorDetail, ResearchState, SubClaim
from app.providers.search.tavily_search import TavilySearchProvider


def test_workflow_router_stops_after_agent_error():
    state = ResearchState(query="A test query")
    assert _route_after_agent(state) == "continue"

    state.error = ErrorDetail(
        stage=AgentName.PLANNER,
        message="Planner failed",
        recoverable=False,
        retry_count=0,
    )
    assert _route_after_agent(state) == "stop"


@pytest.mark.asyncio
async def test_verifier_fails_closed_when_a_claim_request_fails():
    state = ResearchState(query="A test query")
    state.sub_claims = [SubClaim(text="A claim", rationale="A reason")]
    verifier = Verifier(llm=None)
    verifier._verify_claim = AsyncMock(side_effect=TimeoutError("provider timed out"))

    with pytest.raises(RuntimeError, match="Verification failed for one or more claims"):
        await verifier._verify_all(state)

    assert state.agent_status[AgentName.VERIFICATION] == AgentStatus.ERROR
    assert state.error is not None
    assert state.verification_results == []


@pytest.mark.asyncio
async def test_tavily_all_query_failures_raise_instead_of_looking_like_no_results():
    provider = object.__new__(TavilySearchProvider)
    provider.client = SimpleNamespace(search=AsyncMock(side_effect=TimeoutError("Tavily unavailable")))

    with pytest.raises(RuntimeError, match="All 2 Tavily search requests failed"):
        await provider.search_multiple(["first query", "second query"])


@pytest.mark.asyncio
async def test_tavily_successful_empty_search_is_a_valid_empty_result():
    provider = object.__new__(TavilySearchProvider)
    provider.client = SimpleNamespace(search=AsyncMock(return_value={"results": []}))

    assert await provider.search_multiple(["query"]) == []
