Evaluate ONE claim.
Use ONLY the supplied evidence.
Ignore prior knowledge.

Return ONLY valid JSON.
No markdown.
No explanations.
No code fences.

Expected schema:
{
  "status": "...",
  "summary": "...",
  "reasoning": "...",
  "supporting_evidence_ids": [],
  "conflicting_evidence_ids": []
}

Valid status values are: VERIFIED, WEAKLY_SUPPORTED, CONFLICTING, UNSUPPORTED.
The supporting_evidence_ids and conflicting_evidence_ids should contain the IDs of the evidence that support or conflict with the claim.
