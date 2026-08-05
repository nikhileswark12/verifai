from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    contradiction_node,
    planner_node,
    report_node,
    research_node,
    verification_node,
)
from app.models import ResearchState


def build_workflow() -> StateGraph:
    workflow = StateGraph(ResearchState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("research", research_node)
    workflow.add_node("verification", verification_node)
    workflow.add_node("contradiction", contradiction_node)
    workflow.add_node("report", report_node)

    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "research")
    workflow.add_edge("research", "verification")
    workflow.add_edge("verification", "contradiction")
    workflow.add_edge("contradiction", "report")
    workflow.add_edge("report", END)

    return workflow
