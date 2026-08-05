import re
from typing import List

from app.models import Evidence, SourceTier


def _jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate lightweight word-based Jaccard similarity."""
    words1 = set(re.findall(r"\w+", text1.lower()))
    words2 = set(re.findall(r"\w+", text2.lower()))
    if not words1 or not words2:
        return 0.0
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return intersection / union


def _get_tier_score(tier: SourceTier) -> int:
    if tier == SourceTier.HIGH:
        return 3
    if tier == SourceTier.MEDIUM:
        return 2
    return 1


def deduplicate_evidence(evidence: List[Evidence]) -> List[Evidence]:
    """
    Remove duplicate evidence while preserving the highest quality ordering.
    Rules:
    - Same URL -> Duplicate
    - Same Source Domain + Highly similar snippet (>0.75 Jaccard) -> Duplicate
    """
    if not evidence:
        return []

    # Sort evidence by tier (HIGH > MEDIUM > LOW) to ensure we keep the highest quality first
    sorted_evidence = sorted(evidence, key=lambda e: _get_tier_score(e.source.tier), reverse=True)

    unique_evidence: List[Evidence] = []
    seen_urls = set()

    for item in sorted_evidence:
        url = str(item.source.url).strip().lower()
        domain = item.source.domain.lower()
        snippet = item.snippet

        if url in seen_urls:
            continue

        is_duplicate = False
        for unique_item in unique_evidence:
            if unique_item.source.domain.lower() == domain:
                sim = _jaccard_similarity(snippet, unique_item.snippet)
                if sim > 0.75:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            unique_evidence.append(item)
            seen_urls.add(url)

    return unique_evidence
