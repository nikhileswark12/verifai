import uvicorn
from unittest.mock import AsyncMock
import json
import os
import sys
import uuid
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ["ANTHROPIC_API_KEY"] = "dummy"
os.environ["TAVILY_API_KEY"] = "dummy"

from app.services.anthropic_client import AnthropicClient
from app.services.tavily_client import TavilyClient
from app.main import app
from app.dependencies import get_job_store
from datetime import datetime, timezone

async def mock_generate_json(self, system_prompt: str, user_prompt: str, **kwargs):
    if "executive_summary" in system_prompt.lower():
        return {
            "executive_summary": "Mock report summary",
            "overall_assessment": "This is a mock overall assessment.",
            "conclusion": "This is a mock conclusion.",
            "contradiction_summary": "No contradictions found.",
            "claim_summaries": [
                {
                    "claim_id": str(uuid.uuid4()),
                    "summary": "Mock claim summary",
                    "importance": "high"
                }
            ],
            "references": [
                "https://example.com/1"
            ]
        }
    elif "contradict" in system_prompt.lower():
        return {
            "contradiction": True,
            "type": "direct",
            "explanation": "Because I said so.",
            "severity": 1.0
        }
    elif "supporting_evidence_ids" in system_prompt.lower():
        ids = re.findall(r'ID:\s*([a-f0-9\-]+)', user_prompt)
        return {
            "status": "VERIFIED",
            "summary": "This claim is verified mock.",
            "reasoning": "Mock verification reasoning.",
            "supporting_evidence_ids": ids,
            "conflicting_evidence_ids": []
        }
    elif "expand the following sub-claim" in user_prompt.lower() or "queries" in system_prompt.lower():
        return {
            "queries": [
                "mock query 1",
                "mock query 2",
                "mock query 3"
            ]
        }
    elif "sub_claims" in system_prompt.lower():
        return {
            "sub_claims": [
                {"text": "The sky is blue.", "rationale": "Test 1"},
                {"text": "Water is wet.", "rationale": "Test 2"},
                {"text": "Grass is green.", "rationale": "Test 3"}
            ]
        }
    return {}

async def mock_search(self, query: str, *args, **kwargs):
    return [
        {"title": "Mock Source 1", "url": "https://example.com/1", "content": "The sky is indeed blue.", "score": 0.9},
        {"title": "Mock Source 2", "url": "https://example.com/2", "content": "Water is considered wet.", "score": 0.8}
    ]

AnthropicClient.generate_json = mock_generate_json
TavilyClient.search = mock_search

@app.get("/dump/{job_id}")
def dump_job(job_id: str):
    job_store = get_job_store()
    state = job_store.get(job_id)
    if not state:
        return {}
    return json.loads(state.model_dump_json())

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
