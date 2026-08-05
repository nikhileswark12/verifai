export interface AgentDefinition {
  id: "planner" | "research" | "verification" | "contradiction" | "report";
  name: string;
  description: string;
}

export const AGENT_PIPELINE: AgentDefinition[] = [
  {
    id: "planner",
    name: "Planner",
    description: "Breaks the research question into verifiable claims"
  },
  {
    id: "research",
    name: "Research",
    description: "Collects and ranks supporting evidence"
  },
  {
    id: "verification",
    name: "Verification",
    description: "Evaluates evidence against claims"
  },
  {
    id: "contradiction",
    name: "Contradiction",
    description: "Analyzes conflicting information"
  },
  {
    id: "report",
    name: "Report",
    description: "Generates the final research report"
  }
];
