from app.models import ContradictionType, Evidence

def classify_contradiction(
    explanation: str,
    source_a: Evidence,
    source_b: Evidence
) -> ContradictionType:
    exp = explanation.lower().strip()
    if exp == "direct":
        return ContradictionType.DIRECT
    elif exp == "temporal":
        return ContradictionType.TEMPORAL
    elif exp == "contextual":
        return ContradictionType.CONTEXTUAL
    elif exp == "partial":
        return ContradictionType.PARTIAL
    return ContradictionType.NONE

def calculate_contradiction_severity(
    contradiction_type: ContradictionType
) -> float:
    mapping = {
        ContradictionType.DIRECT: 1.0,
        ContradictionType.PARTIAL: 0.6,
        ContradictionType.CONTEXTUAL: 0.3,
        ContradictionType.TEMPORAL: 0.2,
        ContradictionType.NONE: 0.0
    }
    return mapping.get(contradiction_type, 0.0)
