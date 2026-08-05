import type { AgentDefinition } from "../../constants/agents";
import type { MappedAgentStatus } from "../../utils/agentStatus";
import { AgentStatusIcon } from "./AgentStatusIcon";
import { Badge } from "../ui/Badge";

interface AgentCardProps {
  agent: AgentDefinition;
  status: MappedAgentStatus;
}

export function AgentCard({ agent, status }: AgentCardProps) {
  const getBorderColor = () => {
    switch (status) {
      case "active":
        return "border-blue-300 ring-1 ring-blue-100";
      case "completed":
        return "border-emerald-200";
      case "failed":
        return "border-rose-300";
      case "waiting":
      default:
        return "border-slate-200 opacity-60";
    }
  };

  const getBadgeVariant = () => {
    switch (status) {
      case "active": return "warning";
      case "completed": return "success";
      case "failed": return "error";
      case "waiting":
      default: return "neutral";
    }
  };

  return (
    <div className={`flex items-start gap-4 p-4 rounded-xl border bg-white shadow-sm transition-all duration-300 ${getBorderColor()}`}>
      <div className="flex-shrink-0 mt-1">
        <AgentStatusIcon status={status} />
      </div>
      <div className="flex-grow min-w-0">
        <div className="flex items-center justify-between gap-4 mb-1">
          <h4 className="text-sm font-semibold text-slate-900 truncate">
            {agent.name}
          </h4>
          <Badge variant={getBadgeVariant()}>
            {status.toUpperCase()}
          </Badge>
        </div>
        <p className="text-sm text-slate-500">
          {agent.description}
        </p>
      </div>
    </div>
  );
}
