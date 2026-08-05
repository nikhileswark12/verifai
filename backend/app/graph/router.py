from langgraph.graph.state import CompiledStateGraph

from app.graph.workflow import build_workflow
from app.models import ResearchState


def compile_graph() -> CompiledStateGraph:
    workflow = build_workflow()
    return workflow.compile()


def run_graph(state: ResearchState) -> ResearchState:
    graph = compile_graph()
    result = graph.invoke(state)

    if isinstance(result, ResearchState):
        return result
    return ResearchState.model_validate(result)
