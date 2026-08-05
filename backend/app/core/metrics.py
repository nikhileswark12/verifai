from typing import Dict, Any

def record_agent_start(state, agent: str) -> None:
    if "metrics" not in state.metadata:
        state.metadata["metrics"] = {"agents": {}}
    if "agents" not in state.metadata["metrics"]:
        state.metadata["metrics"]["agents"] = {}
        
    state.metadata["metrics"]["agents"][agent] = {
        "status": "running"
    }

def record_agent_completion(state, agent: str, duration: float) -> None:
    if "metrics" not in state.metadata:
        state.metadata["metrics"] = {"agents": {}}
    if "agents" not in state.metadata["metrics"]:
        state.metadata["metrics"]["agents"] = {}
        
    if agent not in state.metadata["metrics"]["agents"]:
        state.metadata["metrics"]["agents"][agent] = {}
        
    state.metadata["metrics"]["agents"][agent].update({
        "duration": duration,
        "status": "completed"
    })
