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
  tier: "high" | "medium" | "low" | "HIGH" | "MEDIUM" | "LOW";
}

export interface Evidence {
  id: string;
  source: Source;
  snippet: string;
}

export interface ConfidenceBreakdown {
  overall_score: number;
  source_count_score: number;
  reliability_score: number;
  agreement_score: number;
  citation_score: number;
}

export interface Claim {
  sub_claim_id: string;
  text: string;
  status: "verified" | "weakly_supported" | "conflicting" | "unsupported" | "VERIFIED" | "WEAKLY_SUPPORTED" | "CONFLICTING" | "UNSUPPORTED";
  evidence: Evidence[];
  confidence: ConfidenceBreakdown & {
    explanation?: string;
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
  overall_assessment?: string;
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
  agent_status?: Record<string, string>;
  error_message?: string | null;
  [key: string]: string | Record<string, string> | null | undefined;
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
