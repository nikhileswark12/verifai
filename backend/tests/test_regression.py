import os
import pytest
from unittest.mock import AsyncMock, patch

os.environ["OPENROUTER_API_KEY"] = "mocked-openrouter-key"
os.environ["TAVILY_API_KEY"] = "mocked-tavily-key"

from app.models import (
    ResearchState, AgentName, AgentStatus, SubClaim, Evidence, Source, SourceTier,
    VerificationResult, ClaimStatus, ConfidenceBreakdown, ContradictionPair,
    ContradictionType, Claim, ResearchReport, ErrorDetail
)
from app.core.execution_manager import execute_workflow
from app.core.confidence import calculate_confidence
from app.agents.planner import Planner
from app.agents.researcher import Researcher
from app.agents.verifier import Verifier
from app.agents.contradiction import Contradiction
from app.agents.reporter import Reporter
from app.providers.llm.fake import FakeLLMProvider
from app.providers.search.fake import FakeSearchProvider


@pytest.fixture
def base_state():
    return ResearchState(query="Is the earth flat?")


@pytest.mark.asyncio
async def test_planner_contract(base_state):
    llm = FakeLLMProvider(response={
        "sub_claims": [
            {"text": "The earth is a sphere.", "rationale": "General scientific consensus."},
            {"text": "Photos from space show it round.", "rationale": "NASA evidence."},
            {"text": "Gravity pulls matter into spheres.", "rationale": "Physics."}
        ]
    })
    planner = Planner(llm=llm)
    result_state = await planner._run_planner(base_state)
    
    assert result_state.agent_status[AgentName.PLANNER] == AgentStatus.DONE
    assert len(result_state.sub_claims) == 3
    assert result_state.sub_claims[0].text == "The earth is a sphere."
    assert result_state.error is None


@pytest.mark.asyncio
async def test_planner_failure(base_state):
    llm = FakeLLMProvider(response={"invalid_key": []})
    planner = Planner(llm=llm)
    result_state = await planner._run_planner(base_state)
    
    assert result_state.agent_status[AgentName.PLANNER] == AgentStatus.ERROR
    assert result_state.error is not None
    assert result_state.error.stage == AgentName.PLANNER


@pytest.mark.asyncio
@patch("app.agents.researcher.expand_query")
async def test_research_contract(mock_expand, base_state):
    base_state.sub_claims = [SubClaim(text="Test claim", rationale="Test")]
    
    mock_expand.return_value = ["Test query", "Test 2", "Test 3"]
    
    from app.providers.search.base import SearchResult
    search = FakeSearchProvider(results=[
        SearchResult(url="https://bbc.com/test", title="Source 1", content="BBC snippet")
    ])
    llm = FakeLLMProvider()
    
    researcher = Researcher(llm=llm, search=search)
    result_state = await researcher._collect_evidence(base_state)
    
    assert result_state.agent_status[AgentName.RESEARCH] == AgentStatus.DONE
    evidence_list = result_state.evidence_by_claim[base_state.sub_claims[0].id]
    assert len(evidence_list) == 1
    
    evidence = evidence_list[0]
    assert evidence.snippet == "BBC snippet"
    assert evidence.source.domain == "bbc.com"
    assert evidence.source.tier == SourceTier.MEDIUM


@pytest.mark.asyncio
async def test_verifier_valid_evidence(base_state):
    claim = SubClaim(text="Test claim")
    source = Source(name="Test", domain="test.com", url="https://test.com", tier=SourceTier.LOW)
    evidence = Evidence(source=source, snippet="Test snippet")
    
    base_state.sub_claims = [claim]
    base_state.evidence_by_claim = {claim.id: [evidence]}
    
    llm = FakeLLMProvider(response={
        "status": "VERIFIED",
        "summary": "Valid summary",
        "supporting_evidence_ids": [evidence.id],
        "conflicting_evidence_ids": [],
        "reasoning": "Looks good."
    })
    
    verifier = Verifier(llm=llm)
    result_state = await verifier._verify_all(base_state)
    
    assert result_state.agent_status[AgentName.VERIFICATION] == AgentStatus.DONE
    assert len(result_state.verification_results) == 1
    assert result_state.verification_results[0].status == ClaimStatus.VERIFIED


@pytest.mark.asyncio
async def test_verifier_invalid_evidence(base_state):
    claim = SubClaim(text="Test claim")
    base_state.sub_claims = [claim]
    base_state.evidence_by_claim = {claim.id: []}
    
    llm = FakeLLMProvider(response={
        "status": "VERIFIED",
        "summary": "Valid summary",
        "supporting_evidence_ids": ["hallucinated-uuid"],
        "conflicting_evidence_ids": [],
        "reasoning": "Fake ID."
    })
    
    verifier = Verifier(llm=llm)
    with pytest.raises(ValueError, match="Unknown supporting evidence ID: hallucinated-uuid"):
        await verifier._verify_all(base_state)


@pytest.mark.asyncio
async def test_contradiction_contract(base_state):
    source = Source(name="Test", domain="test.com", url="https://test.com", tier=SourceTier.LOW)
    ev_a = Evidence(source=source, snippet="A")
    ev_b = Evidence(source=source, snippet="B")
    
    conf = ConfidenceBreakdown(overall_score=50, source_count_score=50, reliability_score=50, agreement_score=50, citation_score=50)
    
    res_a = VerificationResult(claim_id="1", status=ClaimStatus.VERIFIED, reasoning="A", supporting_evidence=[ev_a], confidence=conf)
    res_b = VerificationResult(claim_id="2", status=ClaimStatus.VERIFIED, reasoning="B", supporting_evidence=[ev_b], confidence=conf)
    
    base_state.verification_results = [res_a, res_b]
    
    llm = FakeLLMProvider(response={
        "contradiction": True,
        "type": "direct",
        "explanation": "They conflict directly.",
        "severity": 0.8
    })
    
    contradiction = Contradiction(llm=llm)
    result_state = await contradiction._compare_all(base_state)
    
    assert result_state.agent_status[AgentName.CONTRADICTION] == AgentStatus.DONE
    assert len(result_state.contradictions) == 1
    assert result_state.contradictions[0].contradiction_type == ContradictionType.DIRECT


def test_confidence_engine():
    source_high = Source(name="High", domain="who.int", url="https://who.int", tier=SourceTier.HIGH)
    source_low = Source(name="Low", domain="random.com", url="https://random.com", tier=SourceTier.LOW)
    
    ev_high = Evidence(source=source_high, snippet="Test")
    ev_low = Evidence(source=source_low, snippet="Test")
    
    conf1 = calculate_confidence(supporting_evidence=[ev_high], conflicting_evidence=[])
    assert conf1.reliability_score == 100.0
    assert conf1.agreement_score == 100.0
    
    conf2 = calculate_confidence(supporting_evidence=[ev_high], conflicting_evidence=[ev_low])
    assert conf2.agreement_score == 50.0
    assert conf2.reliability_score == 70.0 
    
    conf3 = calculate_confidence(supporting_evidence=[], conflicting_evidence=[])
    assert conf3.overall_score == 0.0


@pytest.mark.asyncio
async def test_reporter_contract(base_state):
    claim = SubClaim(text="Test")
    conf = ConfidenceBreakdown(overall_score=80, source_count_score=80, reliability_score=80, agreement_score=80, citation_score=80)
    res = VerificationResult(claim_id=claim.id, status=ClaimStatus.VERIFIED, reasoning="Test", confidence=conf)
    
    base_state.sub_claims = [claim]
    base_state.verification_results = [res]
    
    llm = FakeLLMProvider(response={
        "executive_summary": "Exec sum",
        "overall_assessment": "Good",
        "conclusion": "Conc",
        "contradiction_summary": "None",
        "claim_summaries": [{"claim_id": claim.id, "summary": "test", "importance": "high"}],
        "references": []
    })
    
    reporter = Reporter(llm=llm)
    result_state = await reporter._generate_report(base_state)
    
    assert result_state.agent_status[AgentName.REPORT] == AgentStatus.DONE
    assert result_state.report is not None
    assert result_state.report.executive_summary == "Exec sum"
    assert len(result_state.report.claims) == 1


@pytest.mark.asyncio
@patch("app.graph.nodes.planner_agent")
@patch("app.graph.nodes.researcher_agent")
@patch("app.graph.nodes.verifier_agent")
@patch("app.graph.nodes.contradiction_agent")
@patch("app.graph.nodes.reporter_agent")
async def test_complete_workflow(
    mock_reporter, mock_contradiction, mock_verifier, mock_researcher, mock_planner, base_state
):
    # Setup state progression
    async def run_planner(state):
        state.agent_status[AgentName.PLANNER] = AgentStatus.DONE
        state.sub_claims = [
            SubClaim(text="Claim 1", rationale="Test"),
        ]
        return state
    mock_planner.run = AsyncMock(side_effect=run_planner)

    async def run_researcher(state):
        state.agent_status[AgentName.RESEARCH] = AgentStatus.DONE
        return state
    mock_researcher.run = AsyncMock(side_effect=run_researcher)

    async def run_verifier(state):
        state.agent_status[AgentName.VERIFICATION] = AgentStatus.DONE
        return state
    mock_verifier.run = AsyncMock(side_effect=run_verifier)

    async def run_contradiction(state):
        state.agent_status[AgentName.CONTRADICTION] = AgentStatus.DONE
        return state
    mock_contradiction.run = AsyncMock(side_effect=run_contradiction)

    async def run_reporter(state):
        state.agent_status[AgentName.REPORT] = AgentStatus.DONE
        state.report = ResearchReport(
            query="test",
            executive_summary="Exec sum",
            claims=[],
            overall_confidence=100.0,
            conclusion="Conc"
        )
        return state
    mock_reporter.run = AsyncMock(side_effect=run_reporter)
    
    final_state = await execute_workflow(base_state)
    
    assert final_state.error is None, f"Workflow failed with error: {final_state.error.message}"
    
    assert final_state.metadata["execution"]["status"] == "completed"
    assert final_state.agent_status[AgentName.PLANNER] == AgentStatus.DONE
    assert final_state.agent_status[AgentName.RESEARCH] == AgentStatus.DONE
    assert final_state.agent_status[AgentName.VERIFICATION] == AgentStatus.DONE
    assert final_state.agent_status[AgentName.CONTRADICTION] == AgentStatus.DONE
    assert final_state.agent_status[AgentName.REPORT] == AgentStatus.DONE
    assert final_state.report is not None
