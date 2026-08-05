from typing import Optional, List
from app.models import Claim, VerificationResult, ConfidenceBreakdown, ContradictionPair, SubClaim

def build_claim_summary(
    claim: SubClaim,
    verification: Optional[VerificationResult]
) -> dict:
    if not verification:
        return {
            "claim": claim.text,
            "status": "unverified",
            "supporting_sources": 0,
            "conflicting_sources": 0,
            "confidence": 0,
            "explanation": "No verification data available."
        }
    
    explanation = build_confidence_explanation(verification.confidence)
    
    return {
        "claim": claim.text,
        "status": verification.status,
        "supporting_sources": len(verification.supporting_evidence),
        "conflicting_sources": len(verification.conflicting_evidence),
        "confidence": int(verification.confidence.overall_score),
        "explanation": explanation
    }

def build_confidence_explanation(
    confidence: ConfidenceBreakdown
) -> str:
    reasons = []
    
    if confidence.source_count_score >= 80:
        reasons.append("Multiple supporting sources were found.")
    elif confidence.source_count_score > 0:
        reasons.append("A limited number of sources were found.")
    else:
        reasons.append("No supporting sources were found.")
        
    if confidence.reliability_score >= 80:
        reasons.append("Sources have strong reliability ratings.")
    elif confidence.reliability_score >= 50:
        reasons.append("Sources have mixed reliability ratings.")
    elif confidence.source_count_score > 0:
        reasons.append("Sources have weak reliability ratings.")
        
    if confidence.agreement_score >= 80:
        reasons.append("Evidence agreement is high.")
    elif confidence.agreement_score >= 40:
        reasons.append("There is partial disagreement among sources.")
    elif confidence.source_count_score > 0:
        reasons.append("Evidence agreement is poor.")
        
    if confidence.agreement_score >= 80:
        reasons.append("No major contradictions were detected.")
        
    if confidence.overall_score >= 80:
        prefix = "High confidence because:"
    elif confidence.overall_score >= 50:
        prefix = "Moderate confidence because:"
    else:
        prefix = "Low confidence because:"
        
    return f"{prefix}\n- " + "\n- ".join(reasons)

def build_contradiction_summary(
    contradictions: List[ContradictionPair]
) -> List[dict]:
    res = []
    for c in contradictions:
        res.append({
            "type": c.contradiction_type,
            "severity": c.severity,
            "explanation": c.explanation
        })
    return res
