from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base
from app.models import AgentStatus, SourceTier, ClaimStatus, ContradictionType

class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[AgentStatus] = mapped_column(SQLEnum(AgentStatus, name="agent_status_enum", create_type=True), default=AgentStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    overall_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_detail: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    worker_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    agent_status: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    claims: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    logs: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    sub_claims = relationship("SubClaim", back_populates="job", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="job", cascade="all, delete-orphan")
    verification_results = relationship("VerificationResult", back_populates="job", cascade="all, delete-orphan")
    contradictions = relationship("Contradiction", back_populates="job", cascade="all, delete-orphan")
    report = relationship("ResearchReport", back_populates="job", uselist=False, cascade="all, delete-orphan")


class SubClaim(Base):
    __tablename__ = "sub_claims"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("research_jobs.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    job = relationship("ResearchJob", back_populates="sub_claims")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("research_jobs.id"), nullable=False)
    claim_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sub_claims.id"), nullable=True)
    
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str] = mapped_column(String, nullable=False)
    source_domain: Mapped[str] = mapped_column(String, nullable=False)
    source_tier: Mapped[SourceTier] = mapped_column(SQLEnum(SourceTier, name="source_tier_enum", create_type=True), nullable=False)

    job = relationship("ResearchJob", back_populates="evidence")


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("research_jobs.id"), nullable=False)
    claim_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sub_claims.id"), nullable=False)
    
    status: Mapped[ClaimStatus] = mapped_column(SQLEnum(ClaimStatus, name="claim_status_enum", create_type=True), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    supporting_evidence_ids: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    conflicting_evidence_ids: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)

    job = relationship("ResearchJob", back_populates="verification_results")


class Contradiction(Base):
    __tablename__ = "contradictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("research_jobs.id"), nullable=False)
    
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    contradiction_type: Mapped[ContradictionType] = mapped_column(SQLEnum(ContradictionType, name="contradiction_type_enum", create_type=True), nullable=False)
    severity: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_references: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    job = relationship("ResearchJob", back_populates="contradictions")


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("research_jobs.id"), nullable=False, unique=True)
    
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    conclusion: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job = relationship("ResearchJob", back_populates="report")
