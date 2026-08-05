export type MappedAgentStatus = "waiting" | "active" | "completed" | "failed";

export function mapAgentStatus(backendStatus?: string): MappedAgentStatus {
  switch (backendStatus) {
    case "done":
      return "completed";
    case "running":
      return "active";
    case "failed":
    case "error":
      return "failed";
    case "pending":
    default:
      return "waiting";
  }
}
