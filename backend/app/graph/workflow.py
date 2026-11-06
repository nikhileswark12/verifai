from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    contradiction_node,
    planner_node,
    report_node,
    research_node,
    verification_node,
)
from app.models import ResearchState


def _route_after_agent(state: ResearchState) -> str:
    """Stop the graph as soon as an agent records a fatal error."""
    return "stop" if state.error is not None else "continue"


def build_workflow() -> StateGraph:
    workflow = StateGraph(ResearchState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("research", research_node)
    workflow.add_node("verification", verification_node)
    workflow.add_node("contradiction", contradiction_node)
    workflow.add_node("report", report_node)

    workflow.add_edge(START, "planner")
    workflow.add_conditional_edges(
        "planner", _route_after_agent, {"continue": "research", "stop": END}
    )
    workflow.add_conditional_edges(
        "research", _route_after_agent, {"continue": "verification", "stop": END}
    )
    workflow.add_conditional_edges(
        "verification", _route_after_agent, {"continue": "contradiction", "stop": END}
    )
    workflow.add_conditional_edges(
        "contradiction", _route_after_agent, {"continue": "report", "stop": END}
    )
    workflow.add_edge("report", END)

    return workflow
