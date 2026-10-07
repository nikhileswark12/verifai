
from typing import Dict, List, Optional, Any
from app.models import (
    ResearchState, AgentStatus, AgentName, SubClaim, Evidence, VerificationResult, 
    ContradictionPair, ResearchReport, Claim, Source, ErrorDetail, AgentLog, ConfidenceBreakdown, ClaimStatus, ContradictionType, SourceTier
)
from app.db.models import (
    ResearchJob as DBResearchJob,
    SubClaim as DBSubClaim,
    Evidence as DBEvidence,
    VerificationResult as DBVerificationResult,
    Contradiction as DBContradiction,
    ResearchReport as DBResearchReport
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import uuid
from datetime import datetime, timezone

class JobStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, state: ResearchState) -> None:
        db_job = DBResearchJob(
            id=uuid.UUID(state.job_id),
            query=state.query,
            status=state.agent_status.get(AgentName.ORCHESTRATOR, AgentStatus.PENDING),
            created_at=state.created_at,
            overall_confidence=state.report.overall_confidence if state.report else None,
            error_detail=state.error.model_dump(mode='json') if state.error else None,
            agent_status={k.value if hasattr(k, 'value') else k: v.value if hasattr(v, 'value') else v for k, v in state.agent_status.items()},
            claims=[c.model_dump(mode='json') for c in state.claims],
            logs=[l.model_dump(mode='json') for l in state.logs],
            meta_data=state.metadata
        )
        self.session.add(db_job)
        await self.session.commit()

    async def get(self, job_id: str) -> Optional[ResearchState]:
        stmt = (
            select(DBResearchJob)
            .options(
                selectinload(DBResearchJob.sub_claims),
                selectinload(DBResearchJob.evidence),
                selectinload(DBResearchJob.verification_results),
                selectinload(DBResearchJob.contradictions),
                selectinload(DBResearchJob.report)
            )
            .where(DBResearchJob.id == uuid.UUID(job_id))
        )
        result = await self.session.execute(stmt)
        db_job = result.scalar_one_or_none()
        
        if not db_job:
            return None
            
        return self._db_to_state(db_job)

    async def exists(self, job_id: str) -> bool:
        db_job = await self.session.get(DBResearchJob, uuid.UUID(job_id))
        return db_job is not None

    async def claim_job(self, job_id: str, worker_id: str) -> bool:
        """
        Attempts to claim execution ownership of a job using a FOR UPDATE row lock.
        Returns True if the job was successfully claimed (status was PENDING).
        Returns False if the job does not exist or is already claimed/completed.
        """
        stmt = (
            select(DBResearchJob)
            .where(DBResearchJob.id == uuid.UUID(job_id))
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        db_job = result.scalar_one_or_none()
        
        if not db_job:
            return False
            
        current_status = db_job.agent_status.get(AgentName.ORCHESTRATOR.value, AgentStatus.PENDING.value)
        if current_status != AgentStatus.PENDING.value:
            return False
            
        # Claim ownership
        db_job.agent_status[AgentName.ORCHESTRATOR.value] = AgentStatus.RUNNING.value
        
        # Flag JSONB field as modified for SQLAlchemy
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(db_job, "agent_status")
        
        from sqlalchemy.sql import func
        db_job.status = AgentStatus.RUNNING
        db_job.worker_id = worker_id
        db_job.heartbeat_at = func.now()
        
        await self.session.commit()
        return True



    async def record_heartbeat(self, job_id: str, worker_id: str) -> None:
        from sqlalchemy import update
        from sqlalchemy.sql import func
        from app.services.exceptions import JobOwnershipLostError
        
        stmt = (
            update(DBResearchJob)
            .where(DBResearchJob.id == uuid.UUID(job_id))
            .where(DBResearchJob.worker_id == worker_id)
            .values(heartbeat_at=func.now())
        )
        result = await self.session.execute(stmt)
        if result.rowcount == 0:
            # Check if it was because job doesn't exist or ownership lost
            if await self.exists(job_id):
                raise JobOwnershipLostError(f"Worker {worker_id} lost ownership of job {job_id}")
                
        await self.session.commit()

    async def recover_stale_jobs(self, stale_threshold_seconds: int) -> List[str]:
        from sqlalchemy import update, text
        from sqlalchemy.sql import func
        # Raw SQL is easier for interval math in Postgres, but we can also use SQLAlchemy text
        stmt = text(f"""
            UPDATE research_jobs 
            SET status = 'PENDING', 
                worker_id = NULL,
                agent_status = jsonb_set(agent_status, '{{orchestrator}}', '"pending"')
            WHERE status = 'RUNNING' 
              AND heartbeat_at < NOW() - INTERVAL '{stale_threshold_seconds} seconds' 
            RETURNING id
        """)
        result = await self.session.execute(stmt)
        recovered_ids = [str(row[0]) for row in result.fetchall()]
        if recovered_ids:
            await self.session.commit()
        return recovered_ids

    async def update(self, state: ResearchState, worker_id: Optional[str] = None) -> None:
        from app.services.exceptions import JobOwnershipLostError
        
        stmt = (
            select(DBResearchJob)
            .options(
                selectinload(DBResearchJob.sub_claims),
                selectinload(DBResearchJob.evidence),
                selectinload(DBResearchJob.verification_results),
                selectinload(DBResearchJob.contradictions),
                selectinload(DBResearchJob.report)
            )
            .where(DBResearchJob.id == uuid.UUID(state.job_id))
        )
        
        if worker_id is not None:
            stmt = stmt.where(DBResearchJob.worker_id == worker_id)
            
        result = await self.session.execute(stmt)
        db_job = result.scalar_one_or_none()
        
        if not db_job:
            if worker_id is not None and await self.exists(state.job_id):
                raise JobOwnershipLostError(f"Worker {worker_id} lost ownership of job {state.job_id}")
            return

        db_job.status = state.agent_status.get(AgentName.ORCHESTRATOR, AgentStatus.PENDING)
        db_job.overall_confidence = state.report.overall_confidence if state.report else None
        db_job.error_detail = state.error.model_dump(mode='json') if state.error else None
        db_job.agent_status = {k.value if hasattr(k, 'value') else k: v.value if hasattr(v, 'value') else v for k, v in state.agent_status.items()}
        db_job.claims = [c.model_dump(mode='json') for c in state.claims]
        db_job.logs = [l.model_dump(mode='json') for l in state.logs]
        db_job.meta_data = state.metadata

        # Update SubClaims
        db_job.sub_claims.clear()
        for sc in state.sub_claims:
            db_job.sub_claims.append(DBSubClaim(
                id=uuid.UUID(sc.id),
                text=sc.text,
                rationale=sc.rationale
            ))

        # Update Evidence
        db_job.evidence.clear()
        for claim_id, evidence_list in state.evidence_by_claim.items():
            for ev in evidence_list:
                db_job.evidence.append(DBEvidence(
                    id=uuid.UUID(ev.id),
                    claim_id=uuid.UUID(claim_id),
                    snippet=ev.snippet,
                    source_name=ev.source.name,
                    source_url=str(ev.source.url),
                    source_domain=ev.source.domain,
                    source_tier=ev.source.tier
                ))

        # Update VerificationResults
        db_job.verification_results.clear()
        for vr in state.verification_results:
            db_job.verification_results.append(DBVerificationResult(
                id=uuid.UUID(vr.id),
                claim_id=uuid.UUID(vr.claim_id),
                status=vr.status,
                reasoning=vr.reasoning,
                confidence=vr.confidence.model_dump(),
                supporting_evidence_ids=[str(e.id) for e in vr.supporting_evidence],
                conflicting_evidence_ids=[str(e.id) for e in vr.conflicting_evidence]
            ))

        # Update Contradictions
        db_job.contradictions.clear()
        for c in state.contradictions:
            db_job.contradictions.append(DBContradiction(
                id=uuid.UUID(c.id),
                explanation=c.explanation,
                contradiction_type=c.contradiction_type,
                severity=c.severity,
                evidence_references={
                    "source_a": c.source_a.model_dump(mode='json'),
                    "source_b": c.source_b.model_dump(mode='json')
                }
            ))

        # Update Report
        if state.report:
            if not db_job.report:
                db_job.report = DBResearchReport(job_id=db_job.id)
            db_job.report.executive_summary = state.report.executive_summary
            db_job.report.conclusion = state.report.conclusion
            db_job.report.generated_at = state.report.generated_at

        await self.session.commit()
        # To avoid caching issues where an object gets modified later
        # we could also do await self.session.refresh(db_job) but Pydantic holds the real source of truth

    async def list_jobs(self) -> List[ResearchState]:
        stmt = (
            select(DBResearchJob)
            .options(
                selectinload(DBResearchJob.sub_claims),
                selectinload(DBResearchJob.evidence),
                selectinload(DBResearchJob.verification_results),
                selectinload(DBResearchJob.contradictions),
                selectinload(DBResearchJob.report)
            )
        )
        result = await self.session.execute(stmt)
        return [self._db_to_state(job) for job in result.scalars().all()]

    def _db_to_state(self, db_job: DBResearchJob) -> ResearchState:
        # Reconstruct SubClaims
        sub_claims = [
            SubClaim(
                id=str(sc.id),
                text=sc.text,
                rationale=sc.rationale
            ) for sc in db_job.sub_claims
        ]
        
        # Reconstruct Evidence By Claim
        evidence_by_claim = {}
        for ev in db_job.evidence:
            claim_id = str(ev.claim_id) if ev.claim_id else "none"
            if claim_id not in evidence_by_claim:
                evidence_by_claim[claim_id] = []
            
            evidence_by_claim[claim_id].append(
                Evidence(
                    id=str(ev.id),
                    source=Source(
                        name=ev.source_name,
                        domain=ev.source_domain,
                        url=ev.source_url,
                        tier=ev.source_tier
                    ),
                    snippet=ev.snippet,
                    retrieved_at=db_job.created_at # mock fallback for retrieved_at
                )
            )
            
        # Reconstruct VerificationResults
        verification_results = []
        for vr in db_job.verification_results:
            supporting_ids = set(vr.supporting_evidence_ids)
            conflicting_ids = set(vr.conflicting_evidence_ids)
            
            supporting = []
            conflicting = []
            
            claim_evidence = evidence_by_claim.get(str(vr.claim_id), [])
            for e in claim_evidence:
                if e.id in supporting_ids:
                    supporting.append(e)
                if e.id in conflicting_ids:
                    conflicting.append(e)
                    
            verification_results.append(
                VerificationResult(
                    id=str(vr.id),
                    claim_id=str(vr.claim_id),
                    status=vr.status,
                    reasoning=vr.reasoning,
                    confidence=ConfidenceBreakdown(**vr.confidence),
                    supporting_evidence=supporting,
                    conflicting_evidence=conflicting
                )
            )
            
        # Reconstruct Contradictions
        contradictions = []
        for c in db_job.contradictions:
            sa = c.evidence_references.get("source_a", {})
            sb = c.evidence_references.get("source_b", {})
            
            source_a = Evidence.model_validate(sa) if sa else None
            source_b = Evidence.model_validate(sb) if sb else None
            
            if source_a and source_b:
                contradictions.append(
                    ContradictionPair(
                        id=str(c.id),
                        claim_id=str(c.job_id), # Mock since model was refactored
                        source_a=source_a,
                        source_b=source_b,
                        explanation=c.explanation,
                        contradiction_type=c.contradiction_type,
                        severity=c.severity
                    )
                )

        # Reconstruct Claims
        claims = [Claim.model_validate(c) for c in db_job.claims] if db_job.claims else []

        # Reconstruct Report
        report = None
        if db_job.report:
            report = ResearchReport(
                id=str(db_job.report.id),
                query=db_job.query,
                executive_summary=db_job.report.executive_summary,
                claims=claims,
                overall_confidence=db_job.overall_confidence or 0.0,
                conclusion=db_job.report.conclusion,
                generated_at=db_job.report.generated_at
            )

        agent_status = {AgentName(k): AgentStatus(v) for k, v in db_job.agent_status.items()} if db_job.agent_status else {}
        
        return ResearchState(
            job_id=str(db_job.id),
            query=db_job.query,
            created_at=db_job.created_at,
            agent_status=agent_status,
            sub_claims=sub_claims,
            evidence_by_claim=evidence_by_claim,
            verification_results=verification_results,
            contradictions=contradictions,
            claims=claims,
            report=report,
            logs=[AgentLog.model_validate(l) for l in db_job.logs] if db_job.logs else [],
            error=ErrorDetail.model_validate(db_job.error_detail) if db_job.error_detail else None,
            metadata=db_job.meta_data or {}
        )
