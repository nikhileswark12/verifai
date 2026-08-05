"""
VerifAI — Data Models
=====================
Single source of truth for all data structures in VerifAI.
This module strictly contains Pydantic v2 models and Enums.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Generic, List, Literal, Optional, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


def _utcnow() -> datetime:
    """Return a timezone-aware UTC datetime object."""
    return datetime.now(timezone.utc)


def _new_id() -> str:
    """Generate a new UUID4 string."""
    return str(uuid4())


class VerifAIModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=True,
    )


# =====================================================================
# Enums
# =====================================================================

class SourceTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ClaimStatus(str, Enum):
    VERIFIED = "verified"
    WEAKLY_SUPPORTED = "weakly_supported"
    CONFLICTING = "conflicting"
    UNSUPPORTED = "unsupported"

class ContradictionType(str, Enum):
    DIRECT = "direct"
    TEMPORAL = "temporal"
    CONTEXTUAL = "contextual"
    PARTIAL = "partial"
    NONE = "none"


class AgentName(str, Enum):
    ORCHESTRATOR = "orchestrator"
    PLANNER = "planner"
    RESEARCH = "research"
    VERIFICATION = "verification"
    CONTRADICTION = "contradiction"
    REPORT = "report"


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class ResultStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


# =====================================================================
# Core Domain Models
# =====================================================================

class SubClaim(VerifAIModel):
    id: str = Field(default_factory=_new_id)
    text: str
    rationale: Optional[str] = None


class Source(VerifAIModel):
    id: str = Field(default_factory=_new_id)
    name: str
    domain: str
    url: HttpUrl
    tier: SourceTier


class Evidence(VerifAIModel):
    id: str = Field(default_factory=_new_id)
    source: Source
    snippet: str = Field(
        ...,
        max_length=1000,
    )
    retrieved_at: datetime = Field(default_factory=_utcnow)


class ConfidenceBreakdown(VerifAIModel):
    overall_score: float = Field(ge=0, le=100)
    source_count_score: float = Field(ge=0, le=100)
    reliability_score: float = Field(ge=0, le=100)
    agreement_score: float = Field(ge=0, le=100)
    citation_score: float = Field(ge=0, le=100)


class VerificationResult(VerifAIModel):
    id: str = Field(default_factory=_new_id)
    claim_id: str
    status: ClaimStatus
    supporting_evidence: List[Evidence] = Field(default_factory=list)
    conflicting_evidence: List[Evidence] = Field(default_factory=list)
    confidence: ConfidenceBreakdown
    reasoning: str


class ContradictionPair(VerifAIModel):
    id: str = Field(default_factory=_new_id)
    claim_id: str
    source_a: Evidence
    source_b: Evidence
    explanation: str
    contradiction_type: ContradictionType = ContradictionType.NONE
    severity: float = Field(default=0.0, ge=0.0, le=1.0)


class Claim(VerifAIModel):
    id: str = Field(default_factory=_new_id)
    sub_claim_id: str
    text: str
    status: ClaimStatus
    evidence: List[Evidence] = Field(default_factory=list)
    confidence: ConfidenceBreakdown
    contradiction_notes: List[str] = Field(default_factory=list)
    supporting_evidence_count: int = 0
    conflicting_evidence_count: int = 0
    explanation: Optional[str] = None


class ResearchReport(VerifAIModel):
    id: str = Field(default_factory=_new_id)
    query: str
    executive_summary: str
    claims: List[Claim] = Field(default_factory=list)
    overall_confidence: float = Field(
        ...,
        ge=0,
        le=100,
        )
    conclusion: str
    generated_at: datetime = Field(default_factory=_utcnow)


class ErrorDetail(VerifAIModel):
    stage: AgentName
    message: str
    occurred_at: datetime = Field(default_factory=_utcnow)
    recoverable: bool
    retry_count: int = Field(ge=0)


class AgentLog(VerifAIModel):
    timestamp: datetime = Field(default_factory=_utcnow)
    agent: AgentName
    message: str


# =====================================================================
# State Model (LangGraph)
# =====================================================================

class ResearchState(VerifAIModel):
    job_id: str = Field(default_factory=_new_id)
    query: str
    created_at: datetime = Field(default_factory=_utcnow)
    agent_status: Dict[AgentName, AgentStatus] = Field(
        default_factory=lambda: {
            AgentName.PLANNER: AgentStatus.PENDING,
            AgentName.RESEARCH: AgentStatus.PENDING,
            AgentName.VERIFICATION: AgentStatus.PENDING,
            AgentName.CONTRADICTION: AgentStatus.PENDING,
            AgentName.REPORT: AgentStatus.PENDING,
        }
    )
    sub_claims: List[SubClaim] = Field(default_factory=list)
    evidence_by_claim: Dict[str, List[Evidence]] = Field(default_factory=dict)
    verification_results: List[VerificationResult] = Field(default_factory=list)
    contradictions: List[ContradictionPair] = Field(default_factory=list)
    claims: List[Claim] = Field(default_factory=list)
    report: Optional[ResearchReport] = None
    logs: List[AgentLog] = Field(default_factory=list)
    error: Optional[ErrorDetail] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# =====================================================================
# Agent Output & Envelope Models
# =====================================================================

T = TypeVar("T", bound=VerifAIModel)


class AgentResult(VerifAIModel, Generic[T]):
    status: ResultStatus
    agent: AgentName
    data: Optional[T] = None
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=_utcnow)


class PlannerOutput(VerifAIModel):
    sub_claims: List[SubClaim] = Field(default_factory=list)


class ResearchOutput(VerifAIModel):
    evidence_by_claim: Dict[str, List[Evidence]] = Field(default_factory=dict)


class VerificationOutput(VerifAIModel):
    verification_results: List[VerificationResult] = Field(default_factory=list)


class ContradictionOutput(VerifAIModel):
    contradictions: List[ContradictionPair] = Field(default_factory=list)


class ReportOutput(VerifAIModel):
    report: ResearchReport


# Aliases
PlannerResult = AgentResult[PlannerOutput]
ResearchResult = AgentResult[ResearchOutput]
VerificationResultEnvelope = AgentResult[VerificationOutput]
ContradictionResult = AgentResult[ContradictionOutput]
ReportResult = AgentResult[ReportOutput]


# =====================================================================
# API Models
# =====================================================================

class ResearchRequest(VerifAIModel):
    query: str = Field(..., min_length=3, max_length=500)


class ResearchAcceptedResponse(VerifAIModel):
    job_id: str
    status: Literal["accepted"] = "accepted"


class AgentStatusEvent(VerifAIModel):
    job_id: str
    agent: AgentName
    status: AgentStatus
    timestamp: datetime = Field(default_factory=_utcnow)
    detail: Optional[str] = None


class ResearchStatusResponse(VerifAIModel):
    job_id: str
    agent_status: Dict[AgentName, AgentStatus]


class ResearchErrorResponse(VerifAIModel):
    error: Literal[True] = True
    stage: AgentName
    message: str
