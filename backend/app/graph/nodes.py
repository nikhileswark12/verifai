from app.agents import contradiction, planner, reporter, researcher, verifier
from app.models import ResearchState


async def planner_node(state: ResearchState) -> ResearchState:
    return await planner.run(state)


async def research_node(state: ResearchState) -> ResearchState:
    return await researcher.run(state)


async def verification_node(state: ResearchState) -> ResearchState:
    return await verifier.run(state)


async def contradiction_node(state: ResearchState) -> ResearchState:
    return await contradiction.run(state)


async def report_node(state: ResearchState) -> ResearchState:
    return await reporter.run(state)
