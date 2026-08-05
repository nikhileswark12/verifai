from typing import List
from app.models import Evidence, ConfidenceBreakdown, SourceTier

def calculate_confidence(
    supporting_evidence: List[Evidence],
    conflicting_evidence: List[Evidence]
) -> ConfidenceBreakdown:
    all_evidence = supporting_evidence + conflicting_evidence
    total_count = len(all_evidence)
    
    # Citation Completeness Score
    citation_score = 100.0 if total_count > 0 else 0.0
    
    # Evidence Strength Score
    if total_count == 0:
        source_count_score = 0.0
    elif total_count == 1:
        source_count_score = 40.0
    elif total_count == 2:
        source_count_score = 70.0
    else:
        source_count_score = 100.0
        
    # Evidence Agreement Score
    if total_count == 0:
        agreement_score = 0.0
    else:
        agreement_score = (len(supporting_evidence) / total_count) * 100.0
        
    # Source Reliability Score
    if total_count == 0:
        reliability_score = 0.0
    else:
        tier_scores = {
            SourceTier.HIGH: 100.0,
            SourceTier.MEDIUM: 70.0,
            SourceTier.LOW: 40.0
        }
        total_reliability = sum(tier_scores.get(ev.source.tier, 40.0) for ev in all_evidence)
        reliability_score = total_reliability / total_count
        
    # Overall Confidence
    overall_score = (
        (reliability_score * 0.40) +
        (agreement_score * 0.25) +
        (source_count_score * 0.20) +
        (citation_score * 0.15)
    )
    
    return ConfidenceBreakdown(
        overall_score=round(overall_score, 2),
        source_count_score=round(source_count_score, 2),
        reliability_score=round(reliability_score, 2),
        agreement_score=round(agreement_score, 2),
        citation_score=round(citation_score, 2)
    )
