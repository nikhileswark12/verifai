from functools import lru_cache

from app.models import ResearchState
from app.providers.llm.factory import get_llm_provider
from app.providers.search.factory import get_search_provider
from app.agents.contradiction import Contradiction
from app.agents.planner import Planner
from app.agents.reporter import Reporter
from app.agents.researcher import Researcher
from app.agents.verifier import Verifier


@lru_cache(maxsize=1)
def _get_agents():
    llm_provider = get_llm_provider()
    search_provider = get_search_provider()
    return (
        Planner(llm=llm_provider),
        Researcher(llm=llm_provider, search=search_provider),
        Verifier(llm=llm_provider),
        Contradiction(llm=llm_provider),
        Reporter(llm=llm_provider),
    )


async def planner_node(state: ResearchState) -> ResearchState:
    return await _get_agents()[0].run(state)


async def research_node(state: ResearchState) -> ResearchState:
    return await _get_agents()[1].run(state)


async def verification_node(state: ResearchState) -> ResearchState:
    return await _get_agents()[2].run(state)


async def contradiction_node(state: ResearchState) -> ResearchState:
    return await _get_agents()[3].run(state)


async def report_node(state: ResearchState) -> ResearchState:
    return await _get_agents()[4].run(state)
