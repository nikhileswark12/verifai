export type ResearchWorkflowState = "idle" | "submitting" | "running" | "completed" | "error";

export interface ResearchJob {
  job_id: string;
}

export interface AgentStatus {
  planner: string;
  research: string;
  verification: string;
  contradiction: string;
  report: string;
}

export interface Source {
  name: string;
  url: string;
  domain: string;
  tier: "HIGH" | "MEDIUM" | "LOW";
}

export interface Evidence {
  id: string;
  source: Source;
  snippet: string;
}

export interface ConfidenceBreakdown {
  reliability: number;
  agreement: number;
  evidence_strength: number;
  citation_completeness: number;
}

export interface Claim {
  sub_claim_id: string;
  text: string;
  status: "VERIFIED" | "WEAKLY_SUPPORTED" | "CONFLICTING" | "UNSUPPORTED";
  evidence: Evidence[];
  confidence: {
    overall_score: number;
    explanation: string;
    breakdown?: ConfidenceBreakdown;
  };
  contradiction_notes: string[];
  supporting_evidence_count: number;
  conflicting_evidence_count: number;
  explanation: string;
}

export interface ContradictionPair {
  claim_a: string;
  claim_b: string;
  source_a: string;
  source_b: string;
  type: "DIRECT" | "TEMPORAL" | "CONTEXTUAL" | "PARTIAL" | "NONE";
  severity: "HIGH" | "MEDIUM" | "LOW";
  explanation: string;
}

export interface ResearchReport {
  query: string;
  executive_summary: string;
  overall_assessment: string;
  claims: Claim[];
  contradictions?: ContradictionPair[];
  references?: string[];
  overall_confidence: number;
  confidence_breakdown?: ConfidenceBreakdown;
  conclusion: string;
}

export interface ResearchRequest {
  query: string;
}

export interface ResearchAcceptedResponse {
  job_id: string;
}

export interface ResearchStatusResponse {
  job_id?: string;
  status?: string;
  planner?: string;
  research?: string;
  verification?: string;
  contradiction?: string;
  report?: string;
  [key: string]: string | undefined;
}

export interface ResearchResultResponse {
  job_id?: string;
  status?: string;
  report?: ResearchReport;
  error?: string;
}

export interface HealthResponse {
  status: string;
  version?: string;
  timestamp?: string;
  services?: Record<string, string>;
}
