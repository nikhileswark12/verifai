from app.agents.contradiction import Contradiction
from app.agents.planner import Planner
from app.agents.reporter import Reporter
from app.agents.researcher import Researcher
from app.agents.verifier import Verifier
from app.models import ResearchState
from app.providers.llm.factory import get_llm_provider
from app.providers.search.factory import get_search_provider


llm_provider = get_llm_provider()
search_provider = get_search_provider()

planner_agent = Planner(llm=llm_provider)
researcher_agent = Researcher(llm=llm_provider, search=search_provider)
verifier_agent = Verifier(llm=llm_provider)
contradiction_agent = Contradiction(llm=llm_provider)
reporter_agent = Reporter(llm=llm_provider)


async def planner_node(state: ResearchState) -> ResearchState:
    return await planner_agent.run(state)


async def research_node(state: ResearchState) -> ResearchState:
    return await researcher_agent.run(state)


async def verification_node(state: ResearchState) -> ResearchState:
    return await verifier_agent.run(state)


async def contradiction_node(state: ResearchState) -> ResearchState:
    return await contradiction_agent.run(state)


async def report_node(state: ResearchState) -> ResearchState:
    return await reporter_agent.run(state)
