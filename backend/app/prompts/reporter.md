Produce a professional research report.
Do not invent facts.
Use ONLY supplied information.
Do not perform new reasoning.
Do not use outside knowledge.

Return ONLY valid JSON.
No markdown.
No explanations.
No code fences.

Expected structure:
{
  "executive_summary": "...",
  "overall_assessment": "...",
  "claim_summaries": [
    {
      "claim_id": "...",
      "summary": "...",
      "importance": "high"
    }
  ],
  "contradiction_summary": "...",
  "conclusion": "...",
  "references": [
    "https://..."
  ]
}

Note: "references" must be a list of unique, valid URLs used in the research.
If no contradictions exist, explicitly state that no contradictions were detected in "contradiction_summary".
