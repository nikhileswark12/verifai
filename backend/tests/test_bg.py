import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models import ResearchState
from app.graph.router import compile_graph
from app.services.job_store import job_store_instance

async def main():
    state = ResearchState(query="What is the capital of France?")
    job_store_instance.create(state)
    
    graph = compile_graph()
    try:
        async for output in graph.astream(state):
            for node, updated in output.items():
                print(f"Node completed: {node}")
                job_store_instance.update(updated)
    except Exception as e:
        print(f"Exception caught: {e}")
        job_store_instance.update(state)
        
    final_state = job_store_instance.get(state.job_id)
    print(f"Final state job_id: {final_state.job_id}")
    print(f"Final state status: {final_state.agent_status}")
    print(f"Final state logs: {len(final_state.logs)}")

if __name__ == "__main__":
    asyncio.run(main())
